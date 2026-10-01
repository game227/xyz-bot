"""Subscription model.

No online payment — admins/teachers activate subscriptions by hand
(via the bot's "Boshqaruv" menu) after a student submits a
SubscriptionRequest. Expiry is checked lazily on read, same as xyz.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class Subscription(TimeStampedModel):

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Faol'
        EXPIRED = 'EXPIRED', 'Muddati tugagan'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='subscriptions', verbose_name='foydalanuvchi',
    )
    start_date = models.DateField(verbose_name='boshlanish sanasi')
    end_date = models.DateField(verbose_name='tugash sanasi')
    duration_days = models.PositiveIntegerField(verbose_name='davomiyligi (kun)')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE, verbose_name='holati')
    activated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='activated_subscriptions', verbose_name='kim tomonidan faollashtirilgan',
    )

    class Meta:
        verbose_name = 'Obuna'
        verbose_name_plural = 'Obunalar'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.start_date} → {self.end_date} ({self.status})'

    def refresh_status(self):
        if self.status == self.Status.ACTIVE and self.end_date < timezone.localdate():
            self.status = self.Status.EXPIRED
            self.save(update_fields=['status', 'updated_at'])

    def is_currently_active(self):
        self.refresh_status()
        return self.status == self.Status.ACTIVE and self.end_date >= timezone.localdate()


class SubscriptionPricing(TimeStampedModel):
    title = models.CharField(max_length=80, verbose_name='sarlavha')
    price_uzs = models.PositiveIntegerField(verbose_name='narx (so‘m)')
    duration_days = models.PositiveIntegerField(default=30, verbose_name='davomiyligi (kun)')
    is_active = models.BooleanField(default=True, verbose_name='faol')
    order = models.PositiveIntegerField(default=0, verbose_name='tartib')

    class Meta:
        verbose_name = 'Obuna narxi'
        verbose_name_plural = 'Obuna narxlari'
        ordering = ['order', 'duration_days', 'id']

    def __str__(self):
        return f'{self.title} — {self.price_uzs} so‘m / {self.duration_days} kun'

    @property
    def price_label(self):
        return f'{self.price_uzs:,}'.replace(',', ' ') + ' so‘m'


class SubscriptionRequest(TimeStampedModel):

    class Status(models.TextChoices):
        NEW = 'NEW', 'Yangi'
        DONE = 'DONE', 'Bajarildi'
        REJECTED = 'REJECTED', 'Rad etildi'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='subscription_requests', verbose_name='foydalanuvchi',
    )
    plan_days = models.PositiveIntegerField(verbose_name='tarif (kun)')
    note = models.TextField(blank=True, verbose_name='izoh')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW, verbose_name='holat')

    class Meta:
        verbose_name = 'Obuna so‘rovi'
        verbose_name_plural = 'Obuna so‘rovlari'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.plan_days} kun ({self.status})'
