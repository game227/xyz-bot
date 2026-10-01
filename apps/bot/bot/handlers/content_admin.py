"""Kontent boshqaruvi — Fan/Kurs/Modul/Mavzu/Dars/Savol va Obuna tariflari
uchun to'liq CRUD, faqat bot ichida (web panel yo'q). Har bir daraja uchun
alohida handler yozishdan qochish uchun Fan/Kurs/Modul/Mavzu (bir xil
shakl — nom + ota FK) generik callback_data sxemasi orqali boshqariladi:

    cm:<level>:list:<parent_id>   — ro'yxat
    cm:<level>:open:<id>          — bitta element (rename/delete/toggle/ichkariga kirish)
    cm:<level>:add:<parent_id>    — qo'shish oqimini boshlaydi
    cm:<level>:rename:<id>        — nom o'zgartirish oqimini boshlaydi
    cm:<level>:toggle:<id>        — faol/nofaol
    cm:<level>:del:<id>/delyes/delno — o'chirish + tasdiqlash

Dars (lsn) va Savol (q) alohida maydonlari ko'pligi sababli bevosita
yoziladi.
"""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from apps.exam.constants import QUESTIONS_PER_LESSON

from .. import keyboards, services_bridge as services, texts
from ..states import ContentFlow
from .admin import _is_staff

router = Router(name='content_admin')

LEVEL_CRUD = {
    'subj': dict(list=services.list_subjects_admin, create=services.create_subject,
                 rename=services.rename_subject, delete=services.delete_subject,
                 toggle=services.toggle_subject_active, get=services.get_subject, name_attr='name'),
    'crs': dict(list=services.list_courses_admin, create=services.create_course,
                rename=services.rename_course, delete=services.delete_course,
                toggle=services.toggle_course_active, get=services.get_course, name_attr='title'),
    'mod': dict(list=services.list_modules_admin, create=services.create_module,
                rename=services.rename_module, delete=services.delete_module,
                toggle=services.toggle_module_active, get=services.get_module, name_attr='title'),
    'top': dict(list=services.list_topics_admin, create=services.create_topic,
                rename=services.rename_topic, delete=services.delete_topic,
                toggle=services.toggle_topic_active, get=services.get_topic, name_attr='title'),
}
LEVEL_CHILD = {'subj': 'crs', 'crs': 'mod', 'mod': 'top'}
LEVEL_PARENT = {'subj': None, 'crs': 'subj', 'mod': 'crs', 'top': 'mod'}
LEVEL_PARENT_ID_ATTR = {'subj': None, 'crs': 'subject_id', 'mod': 'course_id', 'top': 'module_id'}
LEVEL_TITLE = {
    'subj': texts.CM_SUBJECTS_TITLE, 'crs': texts.CM_COURSES_TITLE,
    'mod': texts.CM_MODULES_TITLE, 'top': texts.CM_TOPICS_TITLE,
}
LEVEL_ASK_ADD = {
    'subj': texts.CM_ASK_SUBJECT_NAME, 'crs': texts.CM_ASK_COURSE_TITLE,
    'mod': texts.CM_ASK_MODULE_TITLE, 'top': texts.CM_ASK_TOPIC_TITLE,
}
LEVEL_ASK_RENAME = {
    'subj': texts.CM_ASK_RENAME_SUBJECT, 'crs': texts.CM_ASK_RENAME_COURSE,
    'mod': texts.CM_ASK_RENAME_MODULE, 'top': texts.CM_ASK_RENAME_TOPIC,
}


def _label(name, is_active):
    return name if is_active else f'{name} (nofaol)'


def _parse(callback):
    # callback_data shakli: cm:<level>:<action>:<id> — id har doim oxirgi bo'lak.
    parts = callback.data.split(':')
    return parts[1], int(parts[-1])


async def _build_list_view(level, parent_id):
    meta = LEVEL_CRUD[level]
    objs = await meta['list'](parent_id)
    items = [(o.id, _label(getattr(o, meta['name_attr']), o.is_active)) for o in objs]
    add_cb = f'cm:{level}:add:{parent_id}'
    parent_level = LEVEL_PARENT[level]
    back_cb = 'admin_back' if parent_level is None else f'cm:{parent_level}:open:{parent_id}'
    kb = keyboards.cm_list_kb(items, prefix=f'cm:{level}:open', add_callback=add_cb, back_callback=back_cb)
    return LEVEL_TITLE[level], kb


async def _build_open_view(level, item_id):
    meta = LEVEL_CRUD[level]
    obj = await meta['get'](item_id)
    if not obj:
        return None, None
    name = getattr(obj, meta['name_attr'])
    parent_attr = LEVEL_PARENT_ID_ATTR[level]
    parent_id = getattr(obj, parent_attr) if parent_attr else 0
    back_cb = f'cm:{level}:list:{parent_id}'

    exam_cb = None
    if level == 'top':
        open_cb, open_label = f'cm:lsn:list:{item_id}', texts.CM_TOPIC_DETAIL_BTN_LESSONS
        exam_cb = f'cm:top:exam:{item_id}'
    else:
        child = LEVEL_CHILD[level]
        open_cb, open_label = f'cm:{child}:list:{item_id}', LEVEL_TITLE[child].rstrip(':')

    kb = keyboards.cm_detail_kb(
        open_cb=open_cb, open_label=open_label, exam_cb=exam_cb,
        toggle_cb=f'cm:{level}:toggle:{item_id}',
        toggle_label=('Faol qilish' if not obj.is_active else 'Nofaol qilish'),
        rename_cb=f'cm:{level}:rename:{item_id}', delete_cb=f'cm:{level}:del:{item_id}',
        back_cb=back_cb,
    )
    return name, kb


async def _deny(callback: CallbackQuery):
    await callback.answer(texts.ADMIN_NO_ACCESS, show_alert=True)


@router.callback_query(F.data == 'admin_back')
async def admin_back(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    await callback.answer()
    await callback.message.edit_text(texts.ADMIN_MENU_TITLE, reply_markup=keyboards.admin_menu_kb())


@router.callback_query(F.data == 'cm_subj')
async def cm_subj_entry(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    await callback.answer()
    text, kb = await _build_list_view('subj', 0)
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.regexp(r'^cm:(subj|crs|mod|top):list:(\d+)$'))
async def cm_list(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    level, parent_id = _parse(callback)
    await callback.answer()
    text, kb = await _build_list_view(level, parent_id)
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.regexp(r'^cm:(subj|crs|mod|top):open:(\d+)$'))
async def cm_open(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    level, item_id = _parse(callback)
    await callback.answer()
    text, kb = await _build_open_view(level, item_id)
    if text is None:
        await callback.message.answer(texts.CM_NOT_FOUND)
        return
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.regexp(r'^cm:(subj|crs|mod|top):add:(\d+)$'))
async def cm_add_start(callback: CallbackQuery, state: FSMContext, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    level, parent_id = _parse(callback)
    await state.update_data(kind=f'{level}_add', parent_id=parent_id)
    await state.set_state(ContentFlow.text_input)
    await callback.answer()
    await callback.message.answer(LEVEL_ASK_ADD[level])


@router.callback_query(F.data.regexp(r'^cm:(subj|crs|mod|top):rename:(\d+)$'))
async def cm_rename_start(callback: CallbackQuery, state: FSMContext, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    level, item_id = _parse(callback)
    await state.update_data(kind=f'{level}_rename', target_id=item_id)
    await state.set_state(ContentFlow.text_input)
    await callback.answer()
    await callback.message.answer(LEVEL_ASK_RENAME[level])


@router.callback_query(F.data.regexp(r'^cm:(subj|crs|mod|top):toggle:(\d+)$'))
async def cm_toggle(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    level, item_id = _parse(callback)
    await LEVEL_CRUD[level]['toggle'](item_id)
    await callback.answer(texts.CM_TOGGLED)
    text, kb = await _build_open_view(level, item_id)
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.regexp(r'^cm:(subj|crs|mod|top):del:(\d+)$'))
async def cm_del_confirm(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    level, item_id = _parse(callback)
    await callback.answer()
    await callback.message.edit_text(
        texts.CM_CONFIRM_DELETE,
        reply_markup=keyboards.confirm_delete_kb(f'cm:{level}:delyes:{item_id}', f'cm:{level}:delno:{item_id}'),
    )


@router.callback_query(F.data.regexp(r'^cm:(subj|crs|mod|top):delyes:(\d+)$'))
async def cm_del_yes(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    level, item_id = _parse(callback)
    meta = LEVEL_CRUD[level]
    obj = await meta['get'](item_id)
    parent_attr = LEVEL_PARENT_ID_ATTR[level]
    parent_id = getattr(obj, parent_attr) if (obj and parent_attr) else 0
    await meta['delete'](item_id)
    await callback.answer(texts.CM_DELETED)
    text, kb = await _build_list_view(level, parent_id)
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.regexp(r'^cm:(subj|crs|mod|top):delno:(\d+)$'))
async def cm_del_no(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    level, item_id = _parse(callback)
    await callback.answer(texts.CM_CANCELLED)
    text, kb = await _build_open_view(level, item_id)
    await callback.message.edit_text(text, reply_markup=kb)


# ---------------------------------------------------------------------------
# Umumiy matn kiritish — qo'shish/nom o'zgartirish oqimlarining oxirgi qadami
# ---------------------------------------------------------------------------

@router.message(ContentFlow.text_input, F.text)
async def cm_text_input(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text:
        await message.answer(texts.CM_EMPTY_TEXT)
        return
    data = await state.get_data()
    kind = data.get('kind', '')

    if kind.endswith('_add') and kind[:-4] in LEVEL_CRUD:
        level = kind[:-4]
        parent_id = data.get('parent_id')
        await state.clear()
        await LEVEL_CRUD[level]['create'](parent_id, text)
        await message.answer(texts.CM_CREATED)
        view_text, kb = await _build_list_view(level, parent_id)
        await message.answer(view_text, reply_markup=kb)
        return

    if kind.endswith('_rename') and kind[:-7] in LEVEL_CRUD:
        level = kind[:-7]
        target_id = data.get('target_id')
        await state.clear()
        await LEVEL_CRUD[level]['rename'](target_id, text)
        await message.answer(texts.CM_RENAMED)
        view_text, kb = await _build_open_view(level, target_id)
        await message.answer(view_text, reply_markup=kb)
        return

    if kind == 'lesson_title':
        await state.update_data(lesson_title=text)
        await state.set_state(ContentFlow.lesson_video)
        await message.answer(texts.CM_ASK_LESSON_VIDEO)
        return

    if kind == 'lsn_rename':
        target_id = data.get('target_id')
        await state.clear()
        await services.rename_lesson(target_id, text)
        await message.answer(texts.CM_RENAMED)
        view_text, kb = await _build_lesson_detail(target_id)
        await message.answer(view_text, reply_markup=kb)
        return

    if kind == 'question_text':
        await state.update_data(question_text=text, answers=[])
        await state.set_state(ContentFlow.question_answer)
        await message.answer(texts.CM_ASK_ANSWER.format(n=1))
        return

    if kind == 'pricing_title':
        await state.update_data(pricing_title=text)
        await state.set_state(ContentFlow.pricing_price)
        await message.answer(texts.CM_ASK_PRICING_PRICE)
        return


# ---------------------------------------------------------------------------
# Dars (Lesson) — nom, video, davomiylik, bepul-sinov
# ---------------------------------------------------------------------------

async def _build_lesson_list(topic_id):
    lessons = await services.list_lessons_admin(topic_id)
    items = [(lesson.id, _label(lesson.title, lesson.is_active)) for lesson in lessons]
    kb = keyboards.cm_list_kb(
        items, prefix='cm:lsn:open', add_callback=f'cm:lsn:add:{topic_id}',
        back_callback=f'cm:top:open:{topic_id}',
    )
    return texts.CM_LESSONS_TITLE, kb


async def _build_lesson_detail(lesson_id):
    lesson = await services.get_lesson(lesson_id)
    if not lesson:
        return None, None
    kb = keyboards.cm_detail_kb(
        open_cb=f'cm:q:list:{lesson_id}', open_label=texts.CM_LESSON_DETAIL_BTN_QUESTIONS,
        toggle_cb=f'cm:lsn:free:{lesson_id}', toggle_label=texts.CM_TOGGLE_FREE_BTN,
        rename_cb=f'cm:lsn:rename:{lesson_id}', delete_cb=f'cm:lsn:del:{lesson_id}',
        back_cb=f'cm:lsn:list:{lesson.topic_id}',
    )
    tag = ' [bepul]' if lesson.is_free_preview else ''
    label = f'{lesson.title}{tag} ({lesson.duration_minutes} daq.)'
    return label, kb


@router.callback_query(F.data.regexp(r'^cm:lsn:list:(\d+)$'))
async def cm_lsn_list(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    topic_id = int(callback.data.split(':')[-1])
    await callback.answer()
    text, kb = await _build_lesson_list(topic_id)
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.regexp(r'^cm:lsn:add:(\d+)$'))
async def cm_lsn_add_start(callback: CallbackQuery, state: FSMContext, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    topic_id = int(callback.data.split(':')[-1])
    await state.update_data(kind='lesson_title', topic_id=topic_id)
    await state.set_state(ContentFlow.text_input)
    await callback.answer()
    await callback.message.answer(texts.CM_ASK_LESSON_TITLE)


@router.message(ContentFlow.lesson_video, F.video | F.document)
async def cm_lesson_video(message: Message, state: FSMContext):
    file_obj = message.video or message.document
    filename = getattr(file_obj, 'file_name', None) or f'{file_obj.file_unique_id}.mp4'
    try:
        buf = await message.bot.download(file_obj.file_id)
    except Exception:
        await message.answer(texts.CM_VIDEO_TOO_LARGE)
        return
    await state.update_data(video_bytes=buf.getvalue(), video_filename=filename)
    await state.set_state(ContentFlow.lesson_duration)
    await message.answer(texts.CM_ASK_LESSON_DURATION)


@router.message(ContentFlow.lesson_video)
async def cm_lesson_video_invalid(message: Message):
    await message.answer(texts.CM_ASK_LESSON_VIDEO)


@router.message(ContentFlow.lesson_duration, F.text)
async def cm_lesson_duration(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit():
        await message.answer(texts.CM_INVALID_NUMBER)
        return
    await state.update_data(lesson_duration=int(text))
    await message.answer(
        texts.CM_ASK_FREE_PREVIEW,
        reply_markup=keyboards.yes_no_kb('lesson_free:yes', 'lesson_free:no'),
    )


@router.callback_query(F.data.startswith('lesson_free:'))
async def cm_lesson_free_choice(callback: CallbackQuery, state: FSMContext):
    is_free = callback.data.split(':')[1] == 'yes'
    data = await state.get_data()
    await state.clear()
    lesson = await services.create_lesson_with_video(
        data['topic_id'], data['lesson_title'], data['lesson_duration'],
        is_free, data['video_bytes'], data['video_filename'],
    )
    await callback.answer()
    if not lesson:
        await callback.message.answer(texts.CM_NOT_FOUND)
        return
    await callback.message.answer(texts.CM_LESSON_CREATED)
    text, kb = await _build_lesson_list(data['topic_id'])
    await callback.message.answer(text, reply_markup=kb)


@router.callback_query(F.data.regexp(r'^cm:lsn:open:(\d+)$'))
async def cm_lsn_open(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    lesson_id = int(callback.data.split(':')[-1])
    await callback.answer()
    text, kb = await _build_lesson_detail(lesson_id)
    if text is None:
        await callback.message.answer(texts.CM_NOT_FOUND)
        return
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.regexp(r'^cm:lsn:free:(\d+)$'))
async def cm_lsn_toggle_free(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    lesson_id = int(callback.data.split(':')[-1])
    await services.toggle_lesson_free_preview(lesson_id)
    await callback.answer(texts.CM_TOGGLED)
    text, kb = await _build_lesson_detail(lesson_id)
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.regexp(r'^cm:lsn:rename:(\d+)$'))
async def cm_lsn_rename_start(callback: CallbackQuery, state: FSMContext, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    lesson_id = int(callback.data.split(':')[-1])
    await state.update_data(kind='lsn_rename', target_id=lesson_id)
    await state.set_state(ContentFlow.text_input)
    await callback.answer()
    await callback.message.answer(texts.CM_ASK_LESSON_TITLE)


@router.callback_query(F.data.regexp(r'^cm:lsn:del:(\d+)$'))
async def cm_lsn_del_confirm(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    lesson_id = int(callback.data.split(':')[-1])
    await callback.answer()
    await callback.message.edit_text(
        texts.CM_CONFIRM_DELETE,
        reply_markup=keyboards.confirm_delete_kb(f'cm:lsn:delyes:{lesson_id}', f'cm:lsn:delno:{lesson_id}'),
    )


@router.callback_query(F.data.regexp(r'^cm:lsn:delyes:(\d+)$'))
async def cm_lsn_del_yes(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    lesson_id = int(callback.data.split(':')[-1])
    lesson = await services.get_lesson(lesson_id)
    topic_id = lesson.topic_id if lesson else 0
    await services.delete_lesson(lesson_id)
    await callback.answer(texts.CM_DELETED)
    text, kb = await _build_lesson_list(topic_id)
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.regexp(r'^cm:lsn:delno:(\d+)$'))
async def cm_lsn_del_no(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    lesson_id = int(callback.data.split(':')[-1])
    await callback.answer(texts.CM_CANCELLED)
    text, kb = await _build_lesson_detail(lesson_id)
    await callback.message.edit_text(text, reply_markup=kb)


# ---------------------------------------------------------------------------
# Test sozlamasi (mavzu bo'yicha o'tish foizi)
# ---------------------------------------------------------------------------

@router.callback_query(F.data.regexp(r'^cm:top:exam:(\d+)$'))
async def cm_top_exam(callback: CallbackQuery, state: FSMContext, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    topic_id = int(callback.data.split(':')[-1])
    settings_obj = await services.get_or_create_exam_settings(topic_id)
    await state.update_data(topic_id=topic_id)
    await state.set_state(ContentFlow.exam_score)
    await callback.answer()
    await callback.message.answer(
        f'Joriy o‘tish foizi: {settings_obj.passing_score}%.\n{texts.CM_ASK_PASSING_SCORE}'
    )


@router.message(ContentFlow.exam_score, F.text)
async def cm_exam_score_input(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit() or not (0 <= int(text) <= 100):
        await message.answer(texts.CM_INVALID_SCORE)
        return
    data = await state.get_data()
    await state.clear()
    await services.set_passing_score(data['topic_id'], int(text))
    await message.answer(texts.CM_SCORE_SAVED.format(score=text))
    view_text, kb = await _build_open_view('top', data['topic_id'])
    await message.answer(view_text, reply_markup=kb)


# ---------------------------------------------------------------------------
# Savol (Question) + 4 ta javob
# ---------------------------------------------------------------------------

async def _build_question_list(lesson_id):
    questions = await services.list_questions_admin(lesson_id)
    lesson = await services.get_lesson(lesson_id)
    _, ready_count = await services.lesson_question_bank_ready(lesson) if lesson else (False, 0)
    items = [(q.id, q.text[:60]) for q in questions]
    kb = keyboards.cm_list_kb(
        items, prefix='cm:q:open', add_callback=f'cm:q:add:{lesson_id}',
        back_callback=f'cm:lsn:open:{lesson_id}',
    )
    title = texts.CM_QUESTIONS_TITLE.format(ready_count=ready_count, needed=QUESTIONS_PER_LESSON)
    return title, kb


@router.callback_query(F.data.regexp(r'^cm:q:list:(\d+)$'))
async def cm_q_list(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    lesson_id = int(callback.data.split(':')[-1])
    await callback.answer()
    text, kb = await _build_question_list(lesson_id)
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.regexp(r'^cm:q:add:(\d+)$'))
async def cm_q_add_start(callback: CallbackQuery, state: FSMContext, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    lesson_id = int(callback.data.split(':')[-1])
    await state.update_data(kind='question_text', lesson_id=lesson_id)
    await state.set_state(ContentFlow.text_input)
    await callback.answer()
    await callback.message.answer(texts.CM_ASK_QUESTION_TEXT)


@router.message(ContentFlow.question_answer, F.text)
async def cm_question_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    answers = data.get('answers', [])
    answers.append(message.text.strip()[:500])
    await state.update_data(answers=answers)
    if len(answers) < 4:
        await message.answer(texts.CM_ASK_ANSWER.format(n=len(answers) + 1))
        return
    await message.answer(texts.CM_ASK_CORRECT_ANSWER, reply_markup=keyboards.correct_answer_choice_kb(answers))


@router.callback_query(F.data.startswith('q_correct:'))
async def cm_question_correct_choice(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data.split(':')[1])
    data = await state.get_data()
    await state.clear()
    question, error = await services.create_question_with_answers(
        data['lesson_id'], data['question_text'], data['answers'], idx,
    )
    await callback.answer()
    if error:
        await callback.message.answer(error)
        return
    await callback.message.answer(texts.CM_QUESTION_CREATED)
    text, kb = await _build_question_list(data['lesson_id'])
    await callback.message.answer(text, reply_markup=kb)


@router.callback_query(F.data.regexp(r'^cm:q:open:(\d+)$'))
async def cm_q_open(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    q_id = int(callback.data.split(':')[-1])
    question = await services.get_question(q_id)
    if not question:
        await callback.answer(texts.CM_NOT_FOUND, show_alert=True)
        return
    await callback.answer()
    lines = [question.text, '']
    for answer in question.answers.all():
        mark = ' (to‘g‘ri)' if answer.is_correct else ''
        lines.append(f'- {answer.text}{mark}')
    kb = keyboards.cm_detail_kb(delete_cb=f'cm:q:del:{q_id}', back_cb=f'cm:q:list:{question.lesson_id}')
    await callback.message.edit_text('\n'.join(lines), reply_markup=kb)


@router.callback_query(F.data.regexp(r'^cm:q:del:(\d+)$'))
async def cm_q_delete(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    q_id = int(callback.data.split(':')[-1])
    question = await services.get_question(q_id)
    lesson_id = question.lesson_id if question else 0
    await services.delete_question(q_id)
    await callback.answer(texts.CM_DELETED)
    text, kb = await _build_question_list(lesson_id)
    await callback.message.edit_text(text, reply_markup=kb)


# ---------------------------------------------------------------------------
# Obuna tariflari (SubscriptionPricing)
# ---------------------------------------------------------------------------

async def _build_pricing_list():
    plans = await services.list_pricing_admin()
    items = [
        (p.id, f'{p.title} — {p.price_label} / {p.duration_days} kun' + ('' if p.is_active else ' (nofaol)'))
        for p in plans
    ]
    kb = keyboards.cm_list_kb(items, prefix='cm_price_open', add_callback='cm_price_add', back_callback='admin_back')
    return texts.CM_PRICING_TITLE, kb


@router.callback_query(F.data == 'admin_pricing')
async def pricing_list(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    await callback.answer()
    text, kb = await _build_pricing_list()
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == 'cm_price_add')
async def pricing_add_start(callback: CallbackQuery, state: FSMContext, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    await state.update_data(kind='pricing_title')
    await state.set_state(ContentFlow.text_input)
    await callback.answer()
    await callback.message.answer(texts.CM_ASK_PRICING_TITLE)


@router.message(ContentFlow.pricing_price, F.text)
async def pricing_price_input(message: Message, state: FSMContext):
    text = message.text.strip().replace(' ', '')
    if not text.isdigit():
        await message.answer(texts.CM_INVALID_NUMBER)
        return
    await state.update_data(pricing_price=int(text))
    await state.set_state(ContentFlow.pricing_days)
    await message.answer(texts.CM_ASK_PRICING_DAYS)


@router.message(ContentFlow.pricing_days, F.text)
async def pricing_days_input(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit():
        await message.answer(texts.CM_INVALID_NUMBER)
        return
    data = await state.get_data()
    await state.clear()
    await services.create_pricing(data['pricing_title'], data['pricing_price'], int(text))
    await message.answer(texts.CM_PRICING_CREATED)
    view_text, kb = await _build_pricing_list()
    await message.answer(view_text, reply_markup=kb)


@router.callback_query(F.data.regexp(r'^cm_price_open:(\d+)$'))
async def pricing_open(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    pk = int(callback.data.split(':')[1])
    await callback.answer()
    await callback.message.edit_text(f'Tarif #{pk}', reply_markup=keyboards.pricing_detail_kb(pk))


@router.callback_query(F.data.startswith('price_toggle:'))
async def pricing_toggle(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    pk = int(callback.data.split(':')[1])
    await services.toggle_pricing_active(pk)
    await callback.answer(texts.CM_TOGGLED)
    text, kb = await _build_pricing_list()
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.startswith('price_del:'))
async def pricing_delete(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    pk = int(callback.data.split(':')[1])
    await services.delete_pricing(pk)
    await callback.answer(texts.CM_DELETED)
    text, kb = await _build_pricing_list()
    await callback.message.edit_text(text, reply_markup=kb)
