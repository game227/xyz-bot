"""Telegram botni ishga tushiradi.
Ishga tushirish: python manage.py runbot
Rejim .env dagi BOT_MODE bilan boshqariladi: 'polling' (default, dev) yoki
'webhook' (production, ochiq HTTPS manzil kerak).
"""
import asyncio
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.core.utils import get_logger

logger = get_logger('bot')


class Command(BaseCommand):
    help = 'Telegram botni ishga tushiradi (polling yoki webhook rejimida).'

    def handle(self, *args, **options):
        if not settings.TELEGRAM_BOT_TOKEN:
            raise CommandError('TELEGRAM_BOT_TOKEN .env faylida sozlanmagan.')

        from apps.bot.bot.dispatcher import run_polling, run_webhook

        if settings.BOT_MODE == 'webhook':
            self.stdout.write(self.style.SUCCESS('Bot ishga tushmoqda (webhook)...'))
            asyncio.run(run_webhook())
            return

        self.stdout.write(self.style.SUCCESS('Bot ishga tushmoqda (polling)...'))
        # Kutilmagan chuqur xato (masalan tarmoq butunlay uzilib ketishi)
        # botni butunlay to'xtatib qo'ymasin — bosqichma-bosqich kutib qayta
        # urinadi. Ctrl+C (KeyboardInterrupt) bilan to'xtatiladi.
        backoff = 5
        while True:
            try:
                asyncio.run(run_polling())
                break
            except KeyboardInterrupt:
                break
            except Exception:
                logger.exception('BOT_CRASHED: %s soniyadan so\'ng qayta urinadi', backoff)
                time.sleep(backoff)
                backoff = min(backoff * 2, 300)
