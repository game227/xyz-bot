"""Sync Django ORM / service functions wrapped for use from async aiogram
handlers. Keeps the scoring/access-control logic in exactly one place
(apps.exam.services, apps.progress.services, apps.subscription.services,
apps.live.services) instead of re-implementing it here.
"""
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile

from apps.accounts.models import CustomUser
from apps.education.models import Course, Lesson, Module, Subject, Topic
from apps.exam.constants import QUESTIONS_PER_LESSON
from apps.exam.models import Answer, ExamSettings, Question
from apps.exam import services as exam_services
from apps.progress import services as progress_services
from apps.subscription import services as sub_services
from apps.live import services as live_services
from apps.live.models import LiveSession
from apps.subscription.models import SubscriptionPricing, SubscriptionRequest
from apps.notifications import services as notifications_services


def _a(fn):
    return sync_to_async(fn, thread_sensitive=True)


# --- accounts ---
get_user_by_telegram_id = _a(lambda telegram_id: CustomUser.objects.filter(telegram_id=telegram_id).first())


def _register_student(telegram_id, telegram_username, full_name, phone):
    parts = full_name.strip().split(maxsplit=1)
    first_name = parts[0] if parts else full_name.strip()
    last_name = parts[1] if len(parts) > 1 else ''
    user = CustomUser(
        username=f'tg_{telegram_id}',
        first_name=first_name[:150],
        last_name=last_name[:150],
        phone_number=phone[:20],
        telegram_id=telegram_id,
        telegram_username=telegram_username or '',
        role=CustomUser.Role.STUDENT,
    )
    user.set_unusable_password()
    user.save()
    return user


register_student = _a(_register_student)


def _unblock_user(user):
    if user.telegram_blocked:
        user.telegram_blocked = False
        user.save(update_fields=['telegram_blocked', 'updated_at'])
    return user


unblock_user = _a(_unblock_user)


def _link_staff_account(telegram_id, telegram_username, username, password):
    """Web panel orqali yaratilgan TEACHER/ADMIN akkauntni shu Telegram chatiga bog'laydi."""
    user = CustomUser.objects.filter(
        username=username, role__in=[CustomUser.Role.TEACHER, CustomUser.Role.ADMIN],
        telegram_id__isnull=True,
    ).first()
    if not user or not user.check_password(password):
        return None
    user.telegram_id = telegram_id
    user.telegram_username = telegram_username or ''
    user.save(update_fields=['telegram_id', 'telegram_username', 'updated_at'])
    return user


link_staff_account = _a(_link_staff_account)


def _ensure_admin_from_settings(telegram_id, telegram_username):
    """settings.ADMIN_TELEGRAM_IDS'da ro'yxatdan o'tgan Telegram ID uchun,
    agar hali CustomUser bo'lmasa, avtomatik ADMIN akkaunt yaratadi.
    Mavjud (masalan avval STUDENT sifatida ro'yxatdan o'tgan) akkauntga
    tegilmaydi — buni ongli ravishda `grant_bot_admin` buyrug'i qiladi."""
    user, created = CustomUser.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            'username': f'tg_{telegram_id}',
            'telegram_username': telegram_username or '',
            'role': CustomUser.Role.ADMIN,
            'is_staff': True,
        },
    )
    if created:
        user.set_unusable_password()
        user.save(update_fields=['password'])
    return user


ensure_admin_from_settings = _a(_ensure_admin_from_settings)


# --- education ---
list_subjects = _a(lambda: list(Subject.objects.filter(is_active=True).order_by('name')))
get_subject = _a(lambda pk: Subject.objects.filter(pk=pk).first())
list_courses = _a(lambda subject_id: list(Course.objects.filter(subject_id=subject_id, is_active=True).order_by('order')))
get_course = _a(lambda pk: Course.objects.select_related('subject').filter(pk=pk).first())
list_modules = _a(lambda course_id: list(Module.objects.filter(course_id=course_id, is_active=True).order_by('order')))
get_module = _a(lambda pk: Module.objects.select_related('course__subject').filter(pk=pk).first())
list_topics = _a(lambda module_id: list(Topic.objects.filter(module_id=module_id, is_active=True).order_by('order')))
get_topic = _a(lambda pk: Topic.objects.select_related('module__course__subject').filter(pk=pk).first())
list_lessons = _a(lambda topic_id: list(Lesson.objects.filter(topic_id=topic_id, is_active=True).order_by('order')))
get_lesson = _a(
    lambda pk: Lesson.objects.select_related('topic__module__course__subject').filter(pk=pk).first()
)


def _is_freemium_lesson(lesson):
    free = Lesson.objects.filter(is_active=True, is_free_preview=True).order_by('id').first()
    if not free:
        free = Lesson.objects.filter(is_active=True).order_by('id').first()
    return bool(free and lesson and free.id == lesson.id)


def _can_access_lesson(user, lesson):
    if sub_services.has_active_subscription(user):
        return True
    return _is_freemium_lesson(lesson)


is_freemium_lesson = _a(_is_freemium_lesson)
can_access_lesson = _a(_can_access_lesson)

# --- exam ---
select_questions_for_lesson = _a(exam_services.select_questions_for_lesson)
build_session_payload = _a(exam_services.build_session_payload)
calculate_result = _a(exam_services.calculate_result)
save_attempt = _a(exam_services.save_attempt)
get_question_texts = _a(
    lambda ids: {q.id: q.text for q in Question.objects.filter(id__in=ids)}
)
get_answer_texts = _a(
    lambda ids: {a.id: a.text for a in Answer.objects.filter(id__in=ids)}
)

# --- progress ---
mark_lesson_complete = _a(progress_services.mark_lesson_complete)
can_start_lesson_exam = _a(progress_services.can_start_lesson_exam)
get_dashboard_summary = _a(progress_services.get_dashboard_summary)

# --- subscription ---
get_active_subscription = _a(sub_services.get_active_subscription)
has_active_subscription = _a(sub_services.has_active_subscription)
get_subscription_plans = _a(sub_services.get_subscription_plans)
activate_subscription = _a(sub_services.activate_subscription)
create_subscription_request = _a(sub_services.create_subscription_request)


def _get_plan_by_index(idx):
    plans = sub_services.get_subscription_plans()
    if 0 <= idx < len(plans):
        return plans[idx]
    return None


get_plan_by_index = _a(_get_plan_by_index)

# --- live ---
get_current_live_session = _a(live_services.get_current_live_session)
start_live_session = _a(live_services.start_live_session)


def _end_live_session(session_id):
    session = LiveSession.objects.filter(pk=session_id).first()
    if session:
        session.mark_ended()
    return session


end_live_session = _a(_end_live_session)
get_my_live_session = _a(
    lambda user: LiveSession.objects.filter(host=user, status=LiveSession.Status.LIVE).order_by('-started_at').first()
)

# --- admin: subscription requests ---
list_pending_requests = _a(
    lambda: list(SubscriptionRequest.objects.filter(status='NEW').select_related('user').order_by('created_at')[:10])
)
get_request = _a(lambda pk: SubscriptionRequest.objects.select_related('user').filter(pk=pk).first())


def _approve_request(req_id, admin_user):
    req = SubscriptionRequest.objects.select_related('user').filter(pk=req_id).first()
    if not req:
        return None
    sub_services.activate_subscription(req.user, req.plan_days, activated_by=admin_user)
    req.status = SubscriptionRequest.Status.DONE
    req.save(update_fields=['status', 'updated_at'])
    return req


approve_request = _a(_approve_request)


def _reject_request(req_id):
    req = SubscriptionRequest.objects.filter(pk=req_id).first()
    if not req:
        return None
    req.status = SubscriptionRequest.Status.REJECTED
    req.save(update_fields=['status', 'updated_at'])
    return req


reject_request = _a(_reject_request)

# --- support (savol-javob) ---
create_support_message = _a(notifications_services.create_support_message)
list_unanswered_support_messages = _a(
    lambda: notifications_services.list_support_messages(only_unanswered=True)[:10]
)
answer_support_message = _a(notifications_services.answer_support_message)


# ---------------------------------------------------------------------------
# Kontent boshqaruvi (bot ichidan to'liq CRUD — web panel yo'q, shu yerda
# xyz'dagi barcha kontent-boshqaruv funksiyalari o'rnini bosadi).
# Subject/Course/Module/Topic bir xil shaklga ega (nom + ota FK + tartib),
# shu sababli bitta kichik generator orqali takrorlanishni oldini olamiz.
# ---------------------------------------------------------------------------

def _make_crud(model, *, name_field, parent_field=None):
    def list_all(parent_id=None):
        qs = model.objects.all()
        if parent_field and parent_id is not None:
            qs = qs.filter(**{parent_field: parent_id})
        order = ['order', 'id'] if hasattr(model, 'order') else [name_field]
        return list(qs.order_by(*order))

    def create(parent_id, name):
        kwargs = {name_field: name.strip()[:200]}
        if parent_field:
            kwargs[parent_field] = parent_id
        if hasattr(model, 'order'):
            kwargs['order'] = model.objects.filter(**({parent_field: parent_id} if parent_field else {})).count()
        return model.objects.create(**kwargs)

    def rename(pk, name):
        obj = model.objects.filter(pk=pk).first()
        if obj:
            setattr(obj, name_field, name.strip()[:200])
            obj.save(update_fields=[name_field, 'updated_at'])
        return obj

    def delete(pk):
        model.objects.filter(pk=pk).delete()

    def toggle_active(pk):
        obj = model.objects.filter(pk=pk).first()
        if obj:
            obj.is_active = not obj.is_active
            obj.save(update_fields=['is_active', 'updated_at'])
        return obj

    return {'list': _a(list_all), 'create': _a(create), 'rename': _a(rename),
            'delete': _a(delete), 'toggle_active': _a(toggle_active)}


_subject_crud = _make_crud(Subject, name_field='name')
_course_crud = _make_crud(Course, name_field='title', parent_field='subject_id')
_module_crud = _make_crud(Module, name_field='title', parent_field='course_id')
_topic_crud = _make_crud(Topic, name_field='title', parent_field='module_id')

list_subjects_admin = _subject_crud['list']
create_subject = _subject_crud['create']
rename_subject = _subject_crud['rename']
delete_subject = _subject_crud['delete']
toggle_subject_active = _subject_crud['toggle_active']

list_courses_admin = _course_crud['list']
create_course = _course_crud['create']
rename_course = _course_crud['rename']
delete_course = _course_crud['delete']
toggle_course_active = _course_crud['toggle_active']

list_modules_admin = _module_crud['list']
create_module = _module_crud['create']
rename_module = _module_crud['rename']
delete_module = _module_crud['delete']
toggle_module_active = _module_crud['toggle_active']

list_topics_admin = _topic_crud['list']
create_topic = _topic_crud['create']
rename_topic = _topic_crud['rename']
delete_topic = _topic_crud['delete']
toggle_topic_active = _topic_crud['toggle_active']


# --- Lesson (video FieldFile + qo'shimcha maydonlar tufayli alohida) ---
list_lessons_admin = _a(lambda topic_id: list(Lesson.objects.filter(topic_id=topic_id).order_by('order', 'id')))


def _create_lesson_with_video(topic_id, title, duration_minutes, is_free_preview, video_bytes, video_filename):
    topic = Topic.objects.filter(pk=topic_id).first()
    if not topic:
        return None
    lesson = Lesson(
        topic=topic, title=title.strip()[:200], duration_minutes=duration_minutes,
        is_free_preview=is_free_preview, order=Lesson.objects.filter(topic=topic).count(),
    )
    lesson.video.save(video_filename, ContentFile(video_bytes), save=False)
    lesson.save()
    return lesson


create_lesson_with_video = _a(_create_lesson_with_video)


def _rename_lesson(pk, title):
    obj = Lesson.objects.filter(pk=pk).first()
    if obj:
        obj.title = title.strip()[:200]
        obj.save(update_fields=['title', 'updated_at'])
    return obj


rename_lesson = _a(_rename_lesson)


def _toggle_lesson_free_preview(pk):
    obj = Lesson.objects.filter(pk=pk).first()
    if obj:
        obj.is_free_preview = not obj.is_free_preview
        obj.save(update_fields=['is_free_preview', 'updated_at'])
    return obj


toggle_lesson_free_preview = _a(_toggle_lesson_free_preview)


def _delete_lesson(pk):
    Lesson.objects.filter(pk=pk).delete()


delete_lesson = _a(_delete_lesson)


def _toggle_lesson_active(pk):
    obj = Lesson.objects.filter(pk=pk).first()
    if obj:
        obj.is_active = not obj.is_active
        obj.save(update_fields=['is_active', 'updated_at'])
    return obj


toggle_lesson_active = _a(_toggle_lesson_active)


# --- Question + 4 ta javob ---
list_questions_admin = _a(
    lambda lesson_id: list(Question.objects.filter(lesson_id=lesson_id).prefetch_related('answers').order_by('id'))
)
get_question = _a(
    lambda pk: Question.objects.prefetch_related('answers').filter(pk=pk).first()
)
lesson_question_bank_ready = _a(exam_services.lesson_question_bank_ready)


def _create_question_with_answers(lesson_id, text, answer_texts, correct_index):
    lesson = Lesson.objects.filter(pk=lesson_id).first()
    if not lesson:
        return None, 'Dars topilmadi.'
    active_count = Question.objects.filter(lesson=lesson, is_active=True).count()
    if active_count >= QUESTIONS_PER_LESSON:
        return None, f'Bu dars uchun allaqachon {QUESTIONS_PER_LESSON} ta faol savol bor (limit).'
    question = Question.objects.create(lesson=lesson, topic=lesson.topic, text=text.strip()[:2000])
    for i, ans_text in enumerate(answer_texts):
        Answer.objects.create(
            question=question, text=ans_text.strip()[:500],
            is_correct=(i == correct_index), order=i,
        )
    return question, None


create_question_with_answers = _a(_create_question_with_answers)


def _delete_question(pk):
    Question.objects.filter(pk=pk).delete()


delete_question = _a(_delete_question)


# --- ExamSettings (mavzu bo'yicha o'tish foizi) ---
def _get_or_create_exam_settings(topic_id):
    topic = Topic.objects.filter(pk=topic_id).first()
    if not topic:
        return None
    obj, _ = ExamSettings.objects.get_or_create(topic=topic, defaults={'passing_score': 70})
    return obj


get_or_create_exam_settings = _a(_get_or_create_exam_settings)


def _set_passing_score(topic_id, value):
    topic = Topic.objects.filter(pk=topic_id).first()
    if not topic:
        return None
    obj, _ = ExamSettings.objects.update_or_create(topic=topic, defaults={'passing_score': value})
    return obj


set_passing_score = _a(_set_passing_score)


# --- Obuna tariflari (SubscriptionPricing) ---
list_pricing_admin = _a(lambda: list(SubscriptionPricing.objects.order_by('order', 'id')))


def _create_pricing(title, price_uzs, duration_days):
    return SubscriptionPricing.objects.create(
        title=title.strip()[:80], price_uzs=price_uzs, duration_days=duration_days,
        order=SubscriptionPricing.objects.count(),
    )


create_pricing = _a(_create_pricing)


def _toggle_pricing_active(pk):
    obj = SubscriptionPricing.objects.filter(pk=pk).first()
    if obj:
        obj.is_active = not obj.is_active
        obj.save(update_fields=['is_active', 'updated_at'])
    return obj


toggle_pricing_active = _a(_toggle_pricing_active)


def _delete_pricing(pk):
    SubscriptionPricing.objects.filter(pk=pk).delete()


delete_pricing = _a(_delete_pricing)


# ---------------------------------------------------------------------------
# Xodimlar (rol boshqaruvi) va foydalanuvchilar ro'yxati
# ---------------------------------------------------------------------------

def _find_user_by_identifier(identifier):
    identifier = identifier.strip()
    if identifier.startswith('@'):
        identifier = identifier[1:]
    user = CustomUser.objects.filter(telegram_username__iexact=identifier).first()
    if user:
        return user
    digits = ''.join(ch for ch in identifier if ch.isdigit())
    if len(digits) >= 7:
        return CustomUser.objects.filter(phone_number__icontains=digits[-9:]).first()
    return None


find_user_by_identifier = _a(_find_user_by_identifier)
list_staff = _a(lambda: list(CustomUser.objects.filter(role__in=['TEACHER', 'ADMIN']).order_by('-created_at')))
list_users_admin = _a(lambda: list(CustomUser.objects.order_by('-created_at')[:30]))
get_user = _a(lambda pk: CustomUser.objects.filter(pk=pk).first())


def _set_user_role(pk, role):
    user = CustomUser.objects.filter(pk=pk).first()
    if not user:
        return None
    user.role = role
    user.save(update_fields=['role', 'is_staff', 'updated_at'])
    return user


set_user_role = _a(_set_user_role)


def _toggle_user_active(pk):
    user = CustomUser.objects.filter(pk=pk).first()
    if user:
        user.is_active = not user.is_active
        user.save(update_fields=['is_active', 'updated_at'])
    return user


toggle_user_active = _a(_toggle_user_active)


def _update_user_name(pk, full_name):
    user = CustomUser.objects.filter(pk=pk).first()
    if not user:
        return None
    parts = full_name.strip().split(maxsplit=1)
    user.first_name = parts[0][:150] if parts else ''
    user.last_name = parts[1][:150] if len(parts) > 1 else ''
    user.save(update_fields=['first_name', 'last_name', 'updated_at'])
    return user


update_user_name = _a(_update_user_name)


def _grant_subscription(pk, days, admin_user):
    target = CustomUser.objects.filter(pk=pk).first()
    if not target:
        return None
    return sub_services.activate_subscription(target, days, activated_by=admin_user)


grant_subscription = _a(_grant_subscription)
