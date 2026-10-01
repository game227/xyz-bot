"""Xodimlar (rol boshqaruvi — botdan turib boshqa foydalanuvchini
O'qituvchi/Administrator qilish) va foydalanuvchilar ro'yxati (faqat
ko'rish + progress)."""
import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from .. import keyboards, services_bridge as services, texts
from ..states import StaffFlow, UserFlow
from .admin import _is_staff

router = Router(name='staff')

ROLE_LABELS = {'STUDENT': "O‘quvchi", 'TEACHER': "O‘qituvchi", 'ADMIN': 'Administrator'}


async def _deny(callback: CallbackQuery):
    await callback.answer(texts.ADMIN_NO_ACCESS, show_alert=True)


@router.callback_query(F.data == 'admin_staff')
async def staff_menu(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    await callback.answer()
    await callback.message.edit_text(texts.STAFF_MENU_TITLE, reply_markup=keyboards.staff_menu_kb())


@router.callback_query(F.data == 'staff_list')
async def staff_list(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    await callback.answer()
    staff = await services.list_staff()
    if not staff:
        await callback.message.answer(texts.STAFF_NONE)
        return
    lines = [
        texts.STAFF_ROW.format(
            name=(u.get_full_name() or u.username), role=ROLE_LABELS.get(u.role, u.role),
            phone=u.phone_number or '—',
        )
        for u in staff
    ]
    await callback.message.answer('\n'.join(lines))


@router.callback_query(F.data == 'staff_assign')
async def staff_assign_start(callback: CallbackQuery, state: FSMContext, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    await state.set_state(StaffFlow.identifier)
    await callback.answer()
    await callback.message.answer(texts.STAFF_ASK_IDENTIFIER)


@router.message(StaffFlow.identifier, F.text)
async def staff_assign_lookup(message: Message, state: FSMContext):
    await state.clear()
    target = await services.find_user_by_identifier(message.text)
    if not target:
        await message.answer(texts.STAFF_NOT_FOUND)
        return
    name = target.get_full_name() or target.username
    await message.answer(
        texts.STAFF_FOUND_ROW.format(name=name, phone=target.phone_number or '—', role=ROLE_LABELS.get(target.role, target.role)),
        reply_markup=keyboards.role_choice_kb(target.id),
    )


@router.callback_query(F.data.startswith('role_set:'))
async def role_set(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    _, user_id, role = callback.data.split(':')
    target = await services.set_user_role(int(user_id), role)
    await callback.answer()
    if not target:
        await callback.message.answer(texts.CM_NOT_FOUND)
        return
    name = target.get_full_name() or target.username
    role_label = ROLE_LABELS.get(role, role)
    await callback.message.edit_text(texts.STAFF_ROLE_SET.format(name=name, role=role_label))

    if target.telegram_id and not target.telegram_blocked:
        from apps.bot.telegram_client import send_message
        await asyncio.to_thread(send_message, target.telegram_id, texts.STAFF_ROLE_NOTIFY.format(role=role_label))


# ---------------------------------------------------------------------------
# Foydalanuvchilar (ro'yxat + progress)
# ---------------------------------------------------------------------------

@router.callback_query(F.data == 'admin_users')
async def users_list(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    await callback.answer()
    users = await services.list_users_admin()
    if not users:
        await callback.message.answer(texts.USERS_NONE)
        return
    items = [(u.id, f'{u.get_full_name() or u.username} — {ROLE_LABELS.get(u.role, u.role)}') for u in users]
    await callback.message.edit_text(texts.USERS_TITLE, reply_markup=keyboards.cm_list_kb(
        items, prefix='user_open', back_callback='admin_back',
    ))


async def _render_user_detail(callback: CallbackQuery, user_id: int):
    target = await services.get_user(user_id)
    if not target:
        await callback.message.answer(texts.CM_NOT_FOUND)
        return

    subscription = await services.get_active_subscription(target)
    has_sub = await services.has_active_subscription(target)
    sub_label = f'faol, {subscription.end_date} gacha' if has_sub else "yo‘q"
    summary = await services.get_dashboard_summary(target)

    text = texts.USER_DETAIL.format(
        name=target.get_full_name() or target.username,
        role=ROLE_LABELS.get(target.role, target.role),
        status=('faol' if target.is_active else 'bloklangan'),
        phone=target.phone_number or '—',
        subscription=sub_label,
        completed_topics=summary['completed_topics_count'],
        overall_progress=summary['overall_progress'],
    )
    attempts = summary['recent_attempts']
    if attempts:
        lines = [text, texts.USER_ATTEMPTS_TITLE]
        for a in attempts:
            lines.append(texts.PROGRESS_ATTEMPT_ROW.format(
                lesson=a.lesson.title, score=a.score, date=a.created_at.strftime('%d.%m.%Y'),
            ))
        text = '\n'.join(lines)

    await callback.message.edit_text(text, reply_markup=keyboards.user_detail_kb(user_id))


@router.callback_query(F.data.startswith('user_open:'))
async def user_detail(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    user_id = int(callback.data.split(':')[1])
    await callback.answer()
    await _render_user_detail(callback, user_id)


@router.callback_query(F.data.startswith('user_sub:'))
async def user_sub_start(callback: CallbackQuery, state: FSMContext, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    user_id = int(callback.data.split(':')[1])
    await state.update_data(target_user_id=user_id)
    await state.set_state(UserFlow.subscription_days)
    await callback.answer()
    await callback.message.answer(texts.USER_ASK_SUB_DAYS)


@router.message(UserFlow.subscription_days, F.text)
async def user_sub_days_input(message: Message, state: FSMContext, db_user=None):
    text = message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        await message.answer(texts.CM_INVALID_NUMBER)
        return
    data = await state.get_data()
    await state.clear()
    target_id = data['target_user_id']
    subscription = await services.grant_subscription(target_id, int(text), db_user)
    await message.answer(texts.USER_SUB_GRANTED.format(end_date=subscription.end_date))

    target = await services.get_user(target_id)
    if target.telegram_id and not target.telegram_blocked:
        from apps.bot.telegram_client import send_message
        await asyncio.to_thread(
            send_message, target.telegram_id,
            texts.USER_SUB_NOTIFY.format(end_date=subscription.end_date),
        )


@router.callback_query(F.data.startswith('user_toggle:'))
async def user_toggle(callback: CallbackQuery, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    user_id = int(callback.data.split(':')[1])
    await services.toggle_user_active(user_id)
    await callback.answer(texts.USER_TOGGLED)
    await _render_user_detail(callback, user_id)


@router.callback_query(F.data.startswith('user_rename:'))
async def user_rename_start(callback: CallbackQuery, state: FSMContext, db_user=None):
    if not _is_staff(db_user):
        return await _deny(callback)
    user_id = int(callback.data.split(':')[1])
    await state.update_data(target_user_id=user_id)
    await state.set_state(UserFlow.rename)
    await callback.answer()
    await callback.message.answer(texts.USER_ASK_RENAME)


@router.message(UserFlow.rename, F.text)
async def user_rename_input(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    await services.update_user_name(data['target_user_id'], message.text)
    await message.answer(texts.USER_RENAMED)
