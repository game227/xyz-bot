import re

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from .. import keyboards, services_bridge as services, texts
from ..common import send_main_menu
from ..states import Registration

router = Router(name='registration')

PHONE_RE = re.compile(r'^\+?\d[\d\s\-]{6,18}\d$')


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db_user=None):
    await state.clear()
    if db_user:
        db_user = await services.unblock_user(db_user)
        await message.answer(texts.ALREADY_REGISTERED_BLOCKED_RESET, reply_markup=keyboards.remove_kb())
        await send_main_menu(message, db_user)
        return
    await message.answer(texts.WELCOME)
    await state.set_state(Registration.full_name)


@router.message(Registration.full_name, F.text)
async def on_full_name(message: Message, state: FSMContext):
    full_name = message.text.strip()
    if not full_name or full_name.startswith('/'):
        await message.answer(texts.INVALID_NAME)
        return
    await state.update_data(full_name=full_name)
    await message.answer(texts.ASK_PHONE, reply_markup=keyboards.phone_request_kb())
    await state.set_state(Registration.phone)


@router.message(Registration.full_name)
async def on_full_name_invalid(message: Message):
    await message.answer(texts.INVALID_NAME)


@router.message(Registration.phone, F.contact)
async def on_phone_contact(message: Message, state: FSMContext):
    await _finish_registration(message, state, message.contact.phone_number)


@router.message(Registration.phone, F.text)
async def on_phone_text(message: Message, state: FSMContext):
    text = message.text.strip()
    if not PHONE_RE.match(text):
        await message.answer(texts.INVALID_PHONE, reply_markup=keyboards.phone_request_kb())
        return
    await _finish_registration(message, state, text)


@router.message(Registration.phone)
async def on_phone_invalid(message: Message):
    await message.answer(texts.INVALID_PHONE, reply_markup=keyboards.phone_request_kb())


async def _finish_registration(message: Message, state: FSMContext, phone: str):
    data = await state.get_data()
    full_name = data.get('full_name', '').strip()
    user = await services.register_student(
        telegram_id=message.from_user.id,
        telegram_username=message.from_user.username or '',
        full_name=full_name,
        phone=phone,
    )
    await state.clear()
    await message.answer(
        texts.REGISTER_DONE.format(name=user.first_name or full_name),
        reply_markup=keyboards.remove_kb(),
    )
    await send_main_menu(message, user)


@router.message(Command('staff'))
async def cmd_staff(message: Message, command: CommandObject, db_user=None):
    if db_user:
        await message.answer('Sizning akkauntingiz allaqachon bog‘langan.')
        return
    args = (command.args or '').split(maxsplit=1)
    if len(args) != 2:
        await message.answer(texts.STAFF_LINK_USAGE)
        return
    username, password = args
    user = await services.link_staff_account(
        telegram_id=message.from_user.id,
        telegram_username=message.from_user.username or '',
        username=username,
        password=password,
    )
    if not user:
        await message.answer(texts.STAFF_LINK_INVALID)
        return
    await message.answer(texts.STAFF_LINK_OK.format(role=user.get_role_display()))
    await send_main_menu(message, user)


@router.message(Command('menu'))
async def cmd_menu(message: Message, db_user=None):
    if not db_user:
        await message.answer("Iltimos, avval /start buyrug'i orqali ro'yxatdan o'ting.")
        return
    await send_main_menu(message, db_user)
