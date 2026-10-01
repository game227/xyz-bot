"""Talaba botdan to'g'ridan-to'g'ri savol yuborishi — o'qituvchi/adminlarga
Telegram push qilinadi va web panelda (Bildirishnomalar → Savollar) javob
kutadi."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from .. import keyboards, services_bridge as services, texts
from ..common import require_registration
from ..states import SupportFlow

router = Router(name='support')


@router.message(F.text == texts.BTN_SUPPORT)
async def open_support(message: Message, state: FSMContext, db_user=None):
    if not await require_registration(message, db_user):
        return
    await state.set_state(SupportFlow.message)
    await message.answer(texts.SUPPORT_ASK, reply_markup=keyboards.remove_kb())


@router.message(SupportFlow.message, F.text)
async def receive_support_message(message: Message, state: FSMContext, db_user=None):
    await state.clear()
    await services.create_support_message(db_user, message.text)
    await message.answer(texts.SUPPORT_SENT)
    from ..common import send_main_menu
    await send_main_menu(message, db_user)


@router.message(SupportFlow.message)
async def receive_support_message_invalid(message: Message):
    await message.answer(texts.SUPPORT_EMPTY)
