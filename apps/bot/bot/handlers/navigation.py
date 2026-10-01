from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from .. import keyboards, services_bridge as services, texts
from ..common import require_registration

router = Router(name='navigation')


@router.message(F.text == texts.BTN_SUBJECTS)
async def open_subjects(message: Message, db_user=None):
    if not await require_registration(message, db_user):
        return
    subjects = await services.list_subjects()
    if not subjects:
        await message.answer(texts.NO_SUBJECTS)
        return
    items = [(s.id, s.name) for s in subjects]
    await message.answer('Fanlar:', reply_markup=keyboards.list_kb(items, prefix='subj'))


@router.callback_query(F.data.startswith('subj:'))
async def open_courses(callback: CallbackQuery):
    subject_id = int(callback.data.split(':')[1])
    subject = await services.get_subject(subject_id)
    if not subject:
        await callback.answer('Topilmadi', show_alert=True)
        return
    courses = await services.list_courses(subject_id)
    if not courses:
        await callback.message.edit_text(texts.NO_COURSES, reply_markup=keyboards.list_kb([], prefix='crs', back_callback='back_subjects'))
        await callback.answer()
        return
    items = [(c.id, c.title) for c in courses]
    await callback.message.edit_text(
        f'{subject.name} — kurslar:',
        reply_markup=keyboards.list_kb(items, prefix='crs', back_callback='back_subjects'),
    )
    await callback.answer()


@router.callback_query(F.data == 'back_subjects')
async def back_to_subjects(callback: CallbackQuery):
    subjects = await services.list_subjects()
    items = [(s.id, s.name) for s in subjects]
    await callback.message.edit_text('Fanlar:', reply_markup=keyboards.list_kb(items, prefix='subj'))
    await callback.answer()


@router.callback_query(F.data.startswith('crs:'))
async def open_modules(callback: CallbackQuery):
    course_id = int(callback.data.split(':')[1])
    course = await services.get_course(course_id)
    if not course:
        await callback.answer('Topilmadi', show_alert=True)
        return
    modules = await services.list_modules(course_id)
    back_cb = f'subj:{course.subject_id}'
    if not modules:
        await callback.message.edit_text(texts.NO_MODULES, reply_markup=keyboards.list_kb([], prefix='mod', back_callback=back_cb))
        await callback.answer()
        return
    items = [(m.id, m.title) for m in modules]
    await callback.message.edit_text(
        f'{course.title} — modullar:',
        reply_markup=keyboards.list_kb(items, prefix='mod', back_callback=back_cb),
    )
    await callback.answer()


@router.callback_query(F.data.startswith('mod:'))
async def open_topics(callback: CallbackQuery):
    module_id = int(callback.data.split(':')[1])
    module = await services.get_module(module_id)
    if not module:
        await callback.answer('Topilmadi', show_alert=True)
        return
    topics = await services.list_topics(module_id)
    back_cb = f'crs:{module.course_id}'
    if not topics:
        await callback.message.edit_text(texts.NO_TOPICS, reply_markup=keyboards.list_kb([], prefix='top', back_callback=back_cb))
        await callback.answer()
        return
    items = [(t.id, t.title) for t in topics]
    await callback.message.edit_text(
        f'{module.title} — mavzular:',
        reply_markup=keyboards.list_kb(items, prefix='top', back_callback=back_cb),
    )
    await callback.answer()


@router.callback_query(F.data.startswith('top:'))
async def open_lessons(callback: CallbackQuery):
    topic_id = int(callback.data.split(':')[1])
    topic = await services.get_topic(topic_id)
    if not topic:
        await callback.answer('Topilmadi', show_alert=True)
        return
    lessons = await services.list_lessons(topic_id)
    back_cb = f'mod:{topic.module_id}'
    if not lessons:
        await callback.message.edit_text(texts.NO_LESSONS, reply_markup=keyboards.list_kb([], prefix='lsn', back_callback=back_cb))
        await callback.answer()
        return
    items = []
    for lesson in lessons:
        is_free = await services.is_freemium_lesson(lesson)
        tag = texts.LESSON_FREE_TAG if is_free else ''
        items.append((lesson.id, f'{tag} {lesson.title}'.strip()))
    await callback.message.edit_text(
        f'{topic.title} — darslar:',
        reply_markup=keyboards.list_kb(items, prefix='lsn', back_callback=back_cb),
    )
    await callback.answer()
