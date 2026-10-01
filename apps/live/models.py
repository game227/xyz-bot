from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class LiveSession(TimeStampedModel):
    class Status(models.TextChoices):
        LIVE = 'LIVE', 'Jonli'
        ENDED = 'ENDED', 'Tugagan'

    class Platform(models.TextChoices):
        YOUTUBE = 'YOUTUBE', 'YouTube'
        TELEGRAM = 'TELEGRAM', 'Telegram'

    title = models.CharField(max_length=200, verbose_name='sarlavha')
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='hosted_live_sessions', verbose_name='o‘qituvchi',
    )
    platform = models.CharField(max_length=20, choices=Platform.choices, default=Platform.YOUTUBE, verbose_name='platforma')
    stream_url = models.URLField(verbose_name='efir havolasi')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.LIVE, verbose_name='holat')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='boshlangan')
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name='tugagan')

    class Meta:
        verbose_name = 'Jonli efir'
        verbose_name_plural = 'Jonli efirlar'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.get_status_display()})'

    def mark_ended(self):
        self.status = self.Status.ENDED
        self.ended_at = timezone.now()
        self.save(update_fields=['status', 'ended_at', 'updated_at'])
