"""Obuna tugash va faolsizlik eslatmalarini yuboradi.
Kunlik cron/systemd timer bilan ishga tushirish tavsiya etiladi:
    python manage.py send_reminders
"""
from django.core.management.base import BaseCommand

from apps.notifications.services import send_inactivity_reminders, send_subscription_expiry_reminders


class Command(BaseCommand):
    help = 'Obuna tugash va faolsizlik eslatmalarini yuboradi (kuniga bir marta ishga tushirilsin).'

    def handle(self, *args, **options):
        sub_count = send_subscription_expiry_reminders()
        inactivity_count = send_inactivity_reminders()
        self.stdout.write(self.style.SUCCESS(
            f'Obuna eslatmalari: {sub_count} ta, faolsizlik eslatmalari: {inactivity_count} ta yuborildi.'
        ))
