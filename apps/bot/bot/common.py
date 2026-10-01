from aiogram.types import Message

from . import keyboards, texts


async def send_main_menu(message: Message, db_user):
    is_staff = bool(db_user and db_user.can_manage_content)
    await message.answer(texts.MAIN_MENU_TITLE, reply_markup=keyboards.main_menu_kb(is_staff=is_staff))


async def require_registration(message: Message, db_user) -> bool:
    """True bo'lsa davom eting, False bo'lsa /start'ga yo'naltirilgan — handler shu yerda to'xtashi kerak."""
    if db_user:
        return True
    await message.answer("Iltimos, avval /start buyrug'i orqali ro'yxatdan o'ting.")
    return False
