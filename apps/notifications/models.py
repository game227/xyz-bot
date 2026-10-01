"""Support so'rovlari (bot orqali savol yuborish) va eslatmalar jurnali
(bir xil eslatma kuniga bir marta yuborilishini kafolatlash uchun)."""
from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class SupportMessage(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='support_messages', verbose_name='foydalanuvchi',
    )
    message = models.TextField(verbose_name='savol matni')
    is_answered = models.BooleanField(default=False, verbose_name='javob berilgan')
    admin_reply = models.TextField(blank=True, verbose_name='javob matni')
    answered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='answered_support_messages', verbose_name='kim javob berdi',
    )
    answered_at = models.DateTimeField(null=True, blank=True, verbose_name='javob sanasi')

    class Meta:
        verbose_name = 'Savol'
        verbose_name_plural = 'Savol-javoblar'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.message[:40]}'


class ReminderLog(TimeStampedModel):

    class Kind(models.TextChoices):
        SUBSCRIPTION_EXPIRY = 'SUBSCRIPTION_EXPIRY', 'Obuna tugash eslatmasi'
        INACTIVITY = 'INACTIVITY', 'Faolsizlik eslatmasi'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='reminder_logs', verbose_name='foydalanuvchi',
    )
    kind = models.CharField(max_length=30, choices=Kind.choices, verbose_name='turi')
    sent_date = models.DateField(verbose_name='yuborilgan sana')

    class Meta:
        verbose_name = 'Eslatma jurnali'
        verbose_name_plural = 'Eslatmalar jurnali'
        unique_together = ('user', 'kind', 'sent_date')
        ordering = ['-sent_date']

    def __str__(self):
        return f'{self.user} — {self.kind} — {self.sent_date}'
