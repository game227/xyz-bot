"""Berilgan Telegram ID'ga botda (va xohlasa panelda) administrator huquqini
beradi — CustomUser mavjud bo'lmasa yaratadi, mavjud bo'lsa ADMIN qiladi.

    python manage.py grant_bot_admin 7564700491
    python manage.py grant_bot_admin 7564700491 --username akmal --full-name "Akmal Aka"
"""
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import CustomUser


class Command(BaseCommand):
    help = "Telegram ID bo'yicha CustomUser'ni ADMIN qiladi (yo'q bo'lsa yaratadi)."

    def add_arguments(self, parser):
        parser.add_argument('telegram_id', type=int)
        parser.add_argument('--username', default=None, help="Login (default: tg_<telegram_id>)")
        parser.add_argument('--full-name', default='', help="To'liq ism")
        parser.add_argument('--role', default=CustomUser.Role.ADMIN, choices=[CustomUser.Role.ADMIN, CustomUser.Role.TEACHER])

    def handle(self, *args, **options):
        telegram_id = options['telegram_id']
        role = options['role']
        user = CustomUser.objects.filter(telegram_id=telegram_id).first()

        if user:
            user.role = role
            user.is_staff = True
            user.save(update_fields=['role', 'is_staff', 'updated_at'])
            self.stdout.write(self.style.SUCCESS(
                f"Mavjud foydalanuvchi '{user.username}' (telegram_id={telegram_id}) endi {role}."
            ))
            return

        username = options['username'] or f'tg_{telegram_id}'
        if CustomUser.objects.filter(username=username).exists():
            raise CommandError(f"Login '{username}' band. --username bilan boshqa login bering.")

        full_name = options['full_name'].strip()
        parts = full_name.split(maxsplit=1) if full_name else []
        first_name = parts[0] if parts else 'Admin'
        last_name = parts[1] if len(parts) > 1 else ''

        user = CustomUser(
            username=username,
            first_name=first_name[:150],
            last_name=last_name[:150],
            telegram_id=telegram_id,
            role=role,
            is_staff=True,
        )
        user.set_unusable_password()
        user.save()
        self.stdout.write(self.style.SUCCESS(
            f"Yangi {role} yaratildi: login='{username}', telegram_id={telegram_id}.\n"
            f"Panelga parol bilan kirish kerak bo'lsa: python manage.py changepassword {username}"
        ))
