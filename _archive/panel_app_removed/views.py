from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.accounts.models import CustomUser
from apps.education.models import Course, Lesson, Module, Subject, Topic
from apps.exam.models import ExamAttempt, ExamSettings, Question
from apps.exam.services import lesson_question_bank_ready
from apps.live.models import LiveSession
from apps.live.services import get_current_live_session, start_live_session
from apps.notifications.models import SupportMessage
from apps.notifications.services import answer_support_message
from apps.progress.models import LessonProgress, TopicProgress
from apps.subscription.models import Subscription, SubscriptionRequest
from apps.subscription.services import activate_subscription

from .forms import (
    AnswerFormSet, CourseForm, ExamSettingsForm, LessonForm, LiveSessionForm,
    ModuleForm, QuestionForm, SubjectForm, SupportReplyForm, TopicForm,
)
from .mixins import StaffRequiredMixin


def login_view(request):
    if request.user.is_authenticated:
        return redirect('panel:dashboard')
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        if not user.can_manage_content:
            messages.error(request, 'Bu akkaunt boshqaruv paneliga kira olmaydi.')
        else:
            auth_login(request, user)
            return redirect('panel:dashboard')
    return render(request, 'panel/login.html', {'form': form})


def logout_view(request):
    auth_logout(request)
    return redirect('panel:login')


class DashboardView(StaffRequiredMixin, ListView):
    template_name = 'panel/dashboard.html'
    context_object_name = 'pending_requests'

    def get_queryset(self):
        return SubscriptionRequest.objects.filter(status='NEW').select_related('user')[:10]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['stats'] = {
            'subjects': Subject.objects.count(),
            'lessons': Lesson.objects.count(),
            'students': CustomUser.objects.filter(role=CustomUser.Role.STUDENT).count(),
            'active_subscriptions': Subscription.objects.filter(status='ACTIVE').count(),
        }
        ctx['live_session'] = get_current_live_session()
        return ctx


# ---------------------------------------------------------------------------
# Generic CRUD helper (Subject / Course / Module / Topic all share this shape)
# ---------------------------------------------------------------------------

class BaseListView(StaffRequiredMixin, ListView):
    template_name = 'panel/generic_list.html'
    paginate_by = 30


class BaseCreateView(StaffRequiredMixin, CreateView):
    template_name = 'panel/generic_form.html'


class BaseUpdateView(StaffRequiredMixin, UpdateView):
    template_name = 'panel/generic_form.html'


class BaseDeleteView(StaffRequiredMixin, DeleteView):
    template_name = 'panel/generic_confirm_delete.html'


class SubjectListView(BaseListView):
    model = Subject
    context_object_name = 'rows'
    extra_context = {'title': 'Fanlar', 'add_url': 'panel:subject_add', 'edit_url': 'panel:subject_edit', 'delete_url': 'panel:subject_delete'}


class SubjectCreateView(BaseCreateView):
    model = Subject
    form_class = SubjectForm
    success_url = reverse_lazy('panel:subject_list')
    extra_context = {'title': 'Yangi fan'}


class SubjectUpdateView(BaseUpdateView):
    model = Subject
    form_class = SubjectForm
    success_url = reverse_lazy('panel:subject_list')
    extra_context = {'title': 'Fanni tahrirlash'}


class SubjectDeleteView(BaseDeleteView):
    model = Subject
    success_url = reverse_lazy('panel:subject_list')


class CourseListView(BaseListView):
    model = Course
    context_object_name = 'rows'
    extra_context = {'title': 'Kurslar', 'add_url': 'panel:course_add', 'edit_url': 'panel:course_edit', 'delete_url': 'panel:course_delete'}


class CourseCreateView(BaseCreateView):
    model = Course
    form_class = CourseForm
    success_url = reverse_lazy('panel:course_list')
    extra_context = {'title': 'Yangi kurs'}


class CourseUpdateView(BaseUpdateView):
    model = Course
    form_class = CourseForm
    success_url = reverse_lazy('panel:course_list')
    extra_context = {'title': 'Kursni tahrirlash'}


class CourseDeleteView(BaseDeleteView):
    model = Course
    success_url = reverse_lazy('panel:course_list')


class ModuleListView(BaseListView):
    model = Module
    context_object_name = 'rows'
    extra_context = {'title': 'Modullar', 'add_url': 'panel:module_add', 'edit_url': 'panel:module_edit', 'delete_url': 'panel:module_delete'}


class ModuleCreateView(BaseCreateView):
    model = Module
    form_class = ModuleForm
    success_url = reverse_lazy('panel:module_list')
    extra_context = {'title': 'Yangi modul'}


class ModuleUpdateView(BaseUpdateView):
    model = Module
    form_class = ModuleForm
    success_url = reverse_lazy('panel:module_list')
    extra_context = {'title': 'Modulni tahrirlash'}


class ModuleDeleteView(BaseDeleteView):
    model = Module
    success_url = reverse_lazy('panel:module_list')


class TopicListView(BaseListView):
    model = Topic
    context_object_name = 'rows'
    extra_context = {'title': 'Mavzular', 'add_url': 'panel:topic_add', 'edit_url': 'panel:topic_edit', 'delete_url': 'panel:topic_delete'}


class TopicCreateView(BaseCreateView):
    model = Topic
    form_class = TopicForm
    success_url = reverse_lazy('panel:topic_list')
    extra_context = {'title': 'Yangi mavzu'}


class TopicUpdateView(BaseUpdateView):
    model = Topic
    form_class = TopicForm
    success_url = reverse_lazy('panel:topic_list')
    extra_context = {'title': 'Mavzuni tahrirlash'}


class TopicDeleteView(BaseDeleteView):
    model = Topic
    success_url = reverse_lazy('panel:topic_list')


# ---------------------------------------------------------------------------
# Lesson (custom: file upload)
# ---------------------------------------------------------------------------

class LessonListView(BaseListView):
    model = Lesson
    context_object_name = 'rows'
    extra_context = {'title': 'Video darslar', 'add_url': 'panel:lesson_add', 'edit_url': 'panel:lesson_edit', 'delete_url': 'panel:lesson_delete'}


class LessonCreateView(BaseCreateView):
    model = Lesson
    form_class = LessonForm
    success_url = reverse_lazy('panel:lesson_list')
    extra_context = {'title': 'Yangi video dars', 'is_multipart': True}

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class LessonUpdateView(BaseUpdateView):
    model = Lesson
    form_class = LessonForm
    success_url = reverse_lazy('panel:lesson_list')
    extra_context = {'title': 'Video darsni tahrirlash', 'is_multipart': True}


class LessonDeleteView(BaseDeleteView):
    model = Lesson
    success_url = reverse_lazy('panel:lesson_list')


# ---------------------------------------------------------------------------
# Question + inline Answers
# ---------------------------------------------------------------------------

class QuestionListView(BaseListView):
    model = Question
    context_object_name = 'rows'
    extra_context = {'title': 'Savollar', 'add_url': 'panel:question_add', 'edit_url': 'panel:question_edit', 'delete_url': 'panel:question_delete'}


def question_form_view(request, pk=None):
    if not (request.user.is_authenticated and request.user.can_manage_content):
        return redirect('panel:login')

    instance = get_object_or_404(Question, pk=pk) if pk else None
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=instance)
        formset = AnswerFormSet(request.POST, instance=instance or Question())
        if form.is_valid():
            question = form.save()
            formset = AnswerFormSet(request.POST, instance=question)
            if formset.is_valid():
                formset.save()
                messages.success(request, 'Savol saqlandi.')
                return redirect('panel:question_list')
    else:
        form = QuestionForm(instance=instance)
        formset = AnswerFormSet(instance=instance)

    bank_status = None
    if instance:
        ready, count = lesson_question_bank_ready(instance.lesson)
        bank_status = {'ready': ready, 'count': count}

    return render(request, 'panel/question_form.html', {
        'form': form, 'formset': formset, 'title': 'Savol' if instance else 'Yangi savol',
        'bank_status': bank_status,
    })


class QuestionDeleteView(BaseDeleteView):
    model = Question
    success_url = reverse_lazy('panel:question_list')


def exam_settings_view(request, topic_id):
    if not (request.user.is_authenticated and request.user.can_manage_content):
        return redirect('panel:login')
    from apps.education.models import Topic as TopicModel
    topic = get_object_or_404(TopicModel, pk=topic_id)
    settings_obj, _ = ExamSettings.objects.get_or_create(topic=topic, defaults={'passing_score': 70})
    if request.method == 'POST':
        form = ExamSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Test sozlamasi saqlandi.')
            return redirect('panel:topic_list')
    else:
        form = ExamSettingsForm(instance=settings_obj)
    return render(request, 'panel/generic_form.html', {'form': form, 'title': f'{topic.title} — test sozlamasi'})


# ---------------------------------------------------------------------------
# Subscription requests
# ---------------------------------------------------------------------------

class SubscriptionRequestListView(StaffRequiredMixin, ListView):
    model = SubscriptionRequest
    template_name = 'panel/subscription_requests.html'
    context_object_name = 'rows'
    paginate_by = 30

    def get_queryset(self):
        return SubscriptionRequest.objects.select_related('user').order_by('-created_at')


def approve_subscription_request(request, pk):
    if not (request.user.is_authenticated and request.user.can_manage_content):
        return redirect('panel:login')
    req = get_object_or_404(SubscriptionRequest, pk=pk)
    if req.status == SubscriptionRequest.Status.NEW:
        activate_subscription(req.user, req.plan_days, activated_by=request.user)
        req.status = SubscriptionRequest.Status.DONE
        req.save(update_fields=['status', 'updated_at'])
        messages.success(request, 'Obuna faollashtirildi.')
    return redirect('panel:subscription_requests')


def reject_subscription_request(request, pk):
    if not (request.user.is_authenticated and request.user.can_manage_content):
        return redirect('panel:login')
    req = get_object_or_404(SubscriptionRequest, pk=pk)
    if req.status == SubscriptionRequest.Status.NEW:
        req.status = SubscriptionRequest.Status.REJECTED
        req.save(update_fields=['status', 'updated_at'])
        messages.success(request, 'So‘rov rad etildi.')
    return redirect('panel:subscription_requests')


# ---------------------------------------------------------------------------
# Live session control
# ---------------------------------------------------------------------------

def live_control_view(request):
    if not (request.user.is_authenticated and request.user.can_manage_content):
        return redirect('panel:login')

    my_session = LiveSession.objects.filter(host=request.user, status=LiveSession.Status.LIVE).order_by('-started_at').first()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'start' and not my_session:
            form = LiveSessionForm(request.POST)
            if form.is_valid():
                session, created = start_live_session(
                    request.user, form.cleaned_data['title'],
                    form.cleaned_data['platform'], form.cleaned_data['stream_url'],
                )
                if created:
                    messages.success(request, 'Jonli efir boshlandi va foydalanuvchilarga xabar yuborildi.')
                else:
                    messages.info(request, 'Sizda allaqachon jonli efir bor.')
            return redirect('panel:live_control')
        if action == 'end' and my_session:
            my_session.mark_ended()
            messages.success(request, 'Efir yakunlandi.')
            return redirect('panel:live_control')

    form = LiveSessionForm()
    return render(request, 'panel/live_control.html', {'session': my_session, 'form': form})


# ---------------------------------------------------------------------------
# Users (read-only) + progress lookup
# ---------------------------------------------------------------------------

class UserListView(StaffRequiredMixin, ListView):
    model = CustomUser
    template_name = 'panel/user_list.html'
    context_object_name = 'rows'
    paginate_by = 50

    def get_queryset(self):
        return CustomUser.objects.order_by('-created_at')


class SupportMessageListView(StaffRequiredMixin, ListView):
    model = SupportMessage
    template_name = 'panel/support_messages.html'
    context_object_name = 'rows'
    paginate_by = 30

    def get_queryset(self):
        return SupportMessage.objects.select_related('user').order_by('is_answered', '-created_at')


def support_message_reply(request, pk):
    if not (request.user.is_authenticated and request.user.can_manage_content):
        return redirect('panel:login')
    msg = get_object_or_404(SupportMessage, pk=pk)
    if request.method == 'POST':
        form = SupportReplyForm(request.POST, instance=msg)
        if form.is_valid():
            answer_support_message(msg.pk, request.user, form.cleaned_data['admin_reply'])
            messages.success(request, 'Javob yuborildi.')
            return redirect('panel:support_messages')
    return redirect('panel:support_messages')


# ---------------------------------------------------------------------------
# Statistika
# ---------------------------------------------------------------------------

class StatsView(StaffRequiredMixin, ListView):
    template_name = 'panel/stats.html'
    context_object_name = 'course_rows'

    def get_queryset(self):
        return (
            Course.objects.filter(is_active=True)
            .annotate(lesson_count=models.Count('modules__topics__lessons', distinct=True))
            .order_by('-lesson_count')[:10]
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        attempts = ExamAttempt.objects.all()
        total_attempts = attempts.count()
        passed_attempts = attempts.filter(is_passed=True).count()
        ctx['stats'] = {
            'students': CustomUser.objects.filter(role=CustomUser.Role.STUDENT).count(),
            'teachers': CustomUser.objects.filter(role=CustomUser.Role.TEACHER).count(),
            'active_subscriptions': Subscription.objects.filter(status=Subscription.Status.ACTIVE).count(),
            'lessons_completed': LessonProgress.objects.filter(is_completed=True).count(),
            'topics_completed': TopicProgress.objects.filter(is_completed=True).count(),
            'total_attempts': total_attempts,
            'pass_rate': round(passed_attempts * 100 / total_attempts, 1) if total_attempts else 0,
            'pending_support': SupportMessage.objects.filter(is_answered=False).count(),
            'live_sessions_total': LiveSession.objects.count(),
        }
        return ctx


class UserDetailView(StaffRequiredMixin, ListView):
    template_name = 'panel/user_detail.html'
    context_object_name = 'attempts'

    def get_queryset(self):
        self.target_user = get_object_or_404(CustomUser, pk=self.kwargs['pk'])
        return self.target_user.exam_attempts.select_related('lesson', 'topic').order_by('-created_at')[:20]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['target_user'] = self.target_user
        ctx['lesson_progress'] = LessonProgress.objects.filter(user=self.target_user, is_completed=True).count()
        ctx['topic_progress'] = TopicProgress.objects.filter(user=self.target_user, is_completed=True).count()
        from apps.subscription.services import get_active_subscription
        ctx['subscription'] = get_active_subscription(self.target_user)
        return ctx
