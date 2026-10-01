from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile
from asgiref.sync import sync_to_async
from django.conf import settings

from .. import keyboards, services_bridge as services, texts

router = Router(name='lesson')


@router.callback_query(F.data.startswith('lsn:'))
async def open_lesson(callback: CallbackQuery, db_user=None):
    lesson_id = int(callback.data.split(':')[1])
    lesson = await services.get_lesson(lesson_id)
    if not lesson:
        await callback.answer('Topilmadi', show_alert=True)
        return

    back_cb = f'top:{lesson.topic_id}'
    allowed = await services.can_access_lesson(db_user, lesson)

    caption = f'<b>{lesson.title}</b>\n{lesson.description or ""}'.strip()

    if not allowed:
        await callback.message.edit_text(
            f'{caption}\n\n{texts.LESSON_LOCKED_MSG}',
            reply_markup=keyboards.lesson_detail_kb(
                lesson_id, can_finish=False, can_quiz=False, locked=True, back_callback=back_cb,
            ),
        )
        await callback.answer()
        return

    await callback.answer()
    await callback.message.edit_text(caption, reply_markup=None)
    await _send_lesson_video(callback, lesson)

    can_quiz = await services.can_start_lesson_exam(db_user, lesson)
    await callback.message.answer(
        'Davom etish uchun:',
        reply_markup=keyboards.lesson_detail_kb(
            lesson_id, can_finish=True, can_quiz=can_quiz, locked=False, back_callback=back_cb,
        ),
    )


async def _send_lesson_video(callback: CallbackQuery, lesson):
    if not lesson.video:
        await callback.message.answer(texts.VIDEO_MISSING)
        return

    max_bytes = settings.TELEGRAM_VIDEO_MAX_MB * 1024 * 1024

    @sync_to_async(thread_sensitive=True)
    def _get_size_and_path():
        try:
            size = lesson.video.size
        except (OSError, ValueError):
            return None, None
        try:
            path = lesson.video.path
        except NotImplementedError:
            path = None
        return size, path

    size, path = await _get_size_and_path()

    if size and path and size <= max_bytes:
        try:
            await callback.message.answer_video(FSInputFile(path), caption=lesson.title)
            return
        except (FileNotFoundError, OSError):
            pass

    link = f'{settings.SITE_BASE_URL}{lesson.video.url}'
    await callback.message.answer(texts.VIDEO_TOO_LARGE.format(link=link))


@router.callback_query(F.data.startswith('finish:'))
async def finish_lesson(callback: CallbackQuery, db_user=None):
    lesson_id = int(callback.data.split(':')[1])
    lesson = await services.get_lesson(lesson_id)
    if not lesson:
        await callback.answer('Topilmadi', show_alert=True)
        return
    await services.mark_lesson_complete(db_user, lesson)
    await callback.answer(texts.LESSON_FINISHED_OK, show_alert=True)

    back_cb = f'top:{lesson.topic_id}'
    can_quiz = await services.can_start_lesson_exam(db_user, lesson)
    await callback.message.edit_reply_markup(
        reply_markup=keyboards.lesson_detail_kb(
            lesson_id, can_finish=True, can_quiz=can_quiz, locked=False, back_callback=back_cb,
        )
    )
