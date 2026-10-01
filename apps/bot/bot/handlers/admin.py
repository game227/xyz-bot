"""O'qituvchi/administrator funksiyalari — obuna so'rovlarini tasdiqlash
va jonli efirni boshqarish. Har bir handler db_user.can_manage_content'ni
o'zi tekshiradi (kirish yo'q bo'lsa ADMIN_NO_ACCESS bilan javob beradi)."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from .. import keyboards, services_bridge as services, texts
from ..states import AdminLiveStart, AdminSupportReply

router = Router(name='admin')


def _is_staff(db_user):
    return bool(db_user and db_user.can_manage_content)


@router.message(F.text == texts.BTN_ADMIN)
async def open_admin_menu(message: Message, db_user=None):
    if not _is_staff(db_user):
        await message.answer(texts.ADMIN_NO_ACCESS)
        return
    await message.answer(texts.ADMIN_MENU_TITLE, reply_markup=keyboards.admin_menu_kb())


@router.callback_query(F.data == 'admin_requests')
async def list_requests(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        await callback.answer(texts.ADMIN_NO_ACCESS, show_alert=True)
        return
    await callback.answer()
    requests = await services.list_pending_requests()
    if not requests:
        await callback.message.answer(texts.ADMIN_NO_REQUESTS)
        return
    for req in requests:
        user_label = req.user.get_full_name() or req.user.username
        text = texts.ADMIN_REQ_ROW.format(user=user_label, plan=req.plan_days, note=req.note or '—')
        await callback.message.answer(text, reply_markup=keyboards.request_action_kb(req.id))


@router.callback_query(F.data.startswith('sr_ok:'))
async def approve_request(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        await callback.answer(texts.ADMIN_NO_ACCESS, show_alert=True)
        return
    req_id = int(callback.data.split(':')[1])
    req = await services.approve_request(req_id, db_user)
    if not req:
        await callback.answer('Topilmadi', show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_text(texts.ADMIN_REQ_APPROVED)


@router.callback_query(F.data.startswith('sr_no:'))
async def reject_request(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        await callback.answer(texts.ADMIN_NO_ACCESS, show_alert=True)
        return
    req_id = int(callback.data.split(':')[1])
    req = await services.reject_request(req_id)
    if not req:
        await callback.answer('Topilmadi', show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_text(texts.ADMIN_REQ_REJECTED)


@router.callback_query(F.data == 'admin_live')
async def live_control(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        await callback.answer(texts.ADMIN_NO_ACCESS, show_alert=True)
        return
    await callback.answer()
    session = await services.get_my_live_session(db_user)
    if session:
        await callback.message.answer(
            texts.LIVE_ACTIVE.format(title=session.title, url=session.stream_url),
            reply_markup=keyboards.live_control_kb(has_session=True, session_id=session.id),
        )
    else:
        await callback.message.answer(
            'Hozircha faol efiringiz yo‘q.',
            reply_markup=keyboards.live_control_kb(has_session=False),
        )


@router.callback_query(F.data == 'live_start')
async def live_start_begin(callback: CallbackQuery, state: FSMContext, db_user=None):
    if not _is_staff(db_user):
        await callback.answer(texts.ADMIN_NO_ACCESS, show_alert=True)
        return
    existing = await services.get_my_live_session(db_user)
    if existing:
        await callback.answer(texts.ADMIN_LIVE_ALREADY, show_alert=True)
        return
    await callback.answer()
    await state.set_state(AdminLiveStart.title)
    await callback.message.answer(texts.ADMIN_LIVE_ASK_TITLE)


@router.message(AdminLiveStart.title, F.text)
async def live_start_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip()[:200])
    await state.set_state(AdminLiveStart.platform)
    await message.answer('Platformani tanlang:', reply_markup=keyboards.platform_choice_kb())


@router.callback_query(AdminLiveStart.platform, F.data.startswith('platform:'))
async def live_start_platform(callback: CallbackQuery, state: FSMContext):
    platform = callback.data.split(':')[1]
    await state.update_data(platform=platform)
    await state.set_state(AdminLiveStart.url)
    await callback.answer()
    await callback.message.answer(texts.ADMIN_LIVE_ASK_URL)


@router.message(AdminLiveStart.url, F.text)
async def live_start_url(message: Message, state: FSMContext, db_user=None):
    data = await state.get_data()
    stream_url = message.text.strip()[:200]
    session, created = await services.start_live_session(db_user, data['title'], data['platform'], stream_url)
    await state.clear()
    if created:
        await message.answer(texts.ADMIN_LIVE_STARTED)
    else:
        await message.answer(texts.ADMIN_LIVE_ALREADY)


@router.callback_query(F.data.startswith('live_end:'))
async def live_end(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        await callback.answer(texts.ADMIN_NO_ACCESS, show_alert=True)
        return
    session_id = int(callback.data.split(':')[1])
    await services.end_live_session(session_id)
    await callback.answer()
    await callback.message.edit_text(texts.ADMIN_LIVE_ENDED)


@router.callback_query(F.data == 'admin_support')
async def list_support(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        await callback.answer(texts.ADMIN_NO_ACCESS, show_alert=True)
        return
    await callback.answer()
    messages = await services.list_unanswered_support_messages()
    if not messages:
        await callback.message.answer(texts.ADMIN_SUPPORT_NONE)
        return
    for msg in messages:
        user_label = msg.user.get_full_name() or msg.user.username
        text = texts.ADMIN_SUPPORT_ROW.format(user=user_label, message=msg.message)
        await callback.message.answer(text, reply_markup=keyboards.support_reply_kb(msg.id))


@router.callback_query(F.data.startswith('sup_reply:'))
async def support_reply_begin(callback: CallbackQuery, state: FSMContext, db_user=None):
    if not _is_staff(db_user):
        await callback.answer(texts.ADMIN_NO_ACCESS, show_alert=True)
        return
    message_id = int(callback.data.split(':')[1])
    await state.update_data(support_message_id=message_id)
    await state.set_state(AdminSupportReply.text)
    await callback.answer()
    await callback.message.answer(texts.ADMIN_SUPPORT_ASK_REPLY)


@router.message(AdminSupportReply.text, F.text)
async def support_reply_send(message: Message, state: FSMContext, db_user=None):
    data = await state.get_data()
    message_id = data.get('support_message_id')
    await state.clear()
    if not message_id:
        return
    await services.answer_support_message(message_id, db_user, message.text)
    await message.answer(texts.ADMIN_SUPPORT_REPLIED)
