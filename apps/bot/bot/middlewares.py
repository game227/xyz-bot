"""Har bir xabar/callback uchun joriy CustomUser'ni (agar bog'langan bo'lsa)
data['db_user']ga qo'yadi — har bir handler qayta-qayta so'rov qilmasin uchun.

Bonus: agar xabar yuborayotgan Telegram ID .env'dagi ADMIN_TELEGRAM_IDS
ro'yxatida bo'lsa-yu, hali CustomUser bilan bog'lanmagan bo'lsa, shu yerda
avtomatik ADMIN akkaunt ochib beriladi — ro'yxatdan o'tishni kutmasdan
darhol "Boshqaruv" menyusiga kirish imkonini beradi.
"""
from aiogram import BaseMiddleware
from django.conf import settings

from . import services_bridge as services


class UserMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        tg_user = data.get('event_from_user')
        db_user = await services.get_user_by_telegram_id(tg_user.id) if tg_user else None
        if db_user is None and tg_user and tg_user.id in settings.ADMIN_TELEGRAM_IDS:
            db_user = await services.ensure_admin_from_settings(tg_user.id, tg_user.username or '')
        data['db_user'] = db_user
        return await handler(event, data)
