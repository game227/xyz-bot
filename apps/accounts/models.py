"""Accounts models.

Every end user of this system registers through the Telegram bot itself
(see apps.bot) — CustomUser.telegram_id is the primary identity for
students. TEACHER/ADMIN accounts are granted entirely inside the bot —
an existing ADMIN promotes another user to TEACHER from the bot's
"Boshqaruv" -> "Xodimlar" menu (apps.bot.bot.handlers.staff) — or, for the
very first admin, via `manage.py grant_bot_admin <telegram_id>`.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.models import TimeStampedModel


class CustomUser(AbstractUser, TimeStampedModel):

    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'O‘quvchi'
        TEACHER = 'TEACHER', 'O‘qituvchi'
        ADMIN = 'ADMIN', 'Administrator'

    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='login',
        error_messages={'unique': 'Bu login allaqachon band.'},
    )
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.STUDENT, verbose_name='rol',
    )
    phone_number = models.CharField(max_length=20, blank=True, verbose_name='telefon raqami')
    telegram_id = models.BigIntegerField(
        unique=True, null=True, blank=True, verbose_name='Telegram ID',
    )
    telegram_username = models.CharField(max_length=64, blank=True, verbose_name='Telegram login (@)')
    telegram_blocked = models.BooleanField(
        default=False, verbose_name='botni bloklagan',
        help_text='Xabar yuborishda 403 qaytsa avtomatik True qilinadi.',
    )

    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'
        ordering = ['-created_at']

    def __str__(self):
        return self.get_full_name() or self.username

    def save(self, *args, **kwargs):
        # TEACHER/ADMIN har doim Django /admin/'ga (zaxira interfeys sifatida)
        # kira olishi kerak; STUDENT'ga tushirilganda esa qaytarib olinadi.
        # Superuser'ning is_staff'iga tegilmaydi (u rolga bog'liq emas).
        if not self.is_superuser:
            self.is_staff = self.role in (self.Role.TEACHER, self.Role.ADMIN)
        super().save(*args, **kwargs)

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def can_manage_content(self):
        return self.role in {self.Role.TEACHER, self.Role.ADMIN} or self.is_superuser
