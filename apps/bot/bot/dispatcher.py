import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent
from django.conf import settings

from apps.core.utils import get_logger

from .handlers import (
    admin, content_admin, lesson, live, navigation, progress, quiz,
    registration, staff, subscription, support,
)
from .middlewares import UserMiddleware

logger = get_logger('bot')


def build_bot_and_dispatcher():
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())

    # registration/admin ro'yxatdan avval — /start va /staff har doim ishlashi kerak
    dp.include_router(registration.router)
    dp.include_router(admin.router)
    dp.include_router(content_admin.router)
    dp.include_router(staff.router)
    dp.include_router(navigation.router)
    dp.include_router(lesson.router)
    dp.include_router(quiz.router)
    dp.include_router(progress.router)
    dp.include_router(subscription.router)
    dp.include_router(live.router)
    dp.include_router(support.router)

    dp.errors.register(on_bot_error)

    return bot, dp


async def on_bot_error(event: ErrorEvent):
    """Har qanday handler ichida ushlanmagan xatoni loglaydi va (agar
    sozlangan bo'lsa) admin(lar)ga Telegram orqali qisqacha xabar beradi.
    Foydalanuvchiga esa umumiy, texnik bo'lmagan xabar ko'rsatiladi."""
    logger.exception('BOT_UPDATE_ERROR: update=%s', event.update, exc_info=event.exception)

    from apps.bot.telegram_client import notify_admins
    summary = f'Botda xatolik: {type(event.exception).__name__}: {event.exception}'[:500]
    await asyncio.to_thread(notify_admins, summary)

    update = event.update
    chat = None
    if update.message:
        chat = update.message.chat
    elif update.callback_query and update.callback_query.message:
        chat = update.callback_query.message.chat
    if chat:
        from . import texts
        try:
            await update.bot.send_message(chat.id, texts.ERROR_GENERIC)
        except Exception:
            pass
    return True


async def run_polling():
    bot, dp = build_bot_and_dispatcher()
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info('BOT_STARTED: mode=polling')
    await dp.start_polling(bot)


async def run_webhook():
    """Production rejimi — ochiq HTTPS manzil (settings.WEBHOOK_URL) talab
    qiladi. Dev muhitida (localhost) ishlatib bo'lmaydi, shuning uchun
    default rejim polling."""
    from aiohttp import web
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    if not settings.WEBHOOK_URL:
        raise RuntimeError('BOT_MODE=webhook uchun .env faylida WEBHOOK_URL sozlanishi shart.')

    bot, dp = build_bot_and_dispatcher()
    webhook_url = settings.WEBHOOK_URL + settings.WEBHOOK_PATH
    await bot.set_webhook(
        webhook_url,
        secret_token=settings.WEBHOOK_SECRET or None,
        drop_pending_updates=True,
    )

    app = web.Application()
    SimpleRequestHandler(
        dispatcher=dp, bot=bot, secret_token=settings.WEBHOOK_SECRET or None,
    ).register(app, path=settings.WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.WEBHOOK_LISTEN_HOST, settings.WEBHOOK_LISTEN_PORT)
    await site.start()
    logger.info('BOT_STARTED: mode=webhook url=%s listen=%s:%s', webhook_url, settings.WEBHOOK_LISTEN_HOST, settings.WEBHOOK_LISTEN_PORT)
    await asyncio.Event().wait()
