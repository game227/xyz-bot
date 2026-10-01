from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.education.models import Lesson, Topic


class LessonProgress(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='lesson_progress', verbose_name='foydalanuvchi',
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress_entries', verbose_name='dars')
    is_completed = models.BooleanField(default=False, verbose_name='tugatilgan')
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name='tugatilgan sana')

    class Meta:
        verbose_name = 'Dars progressi'
        verbose_name_plural = 'Dars progresslari'
        unique_together = ('user', 'lesson')

    def __str__(self):
        return f'{self.user} — {self.lesson} — {"tugatilgan" if self.is_completed else "davom etmoqda"}'


class TopicProgress(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='topic_progress', verbose_name='foydalanuvchi',
    )
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='progress_entries', verbose_name='mavzu')
    is_completed = models.BooleanField(default=False, verbose_name='tugatilgan')
    best_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='eng yaxshi natija (%)')
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name='tugatilgan sana')

    class Meta:
        verbose_name = 'Mavzu progressi'
        verbose_name_plural = 'Mavzu progresslari'
        unique_together = ('user', 'topic')

    def __str__(self):
        return f'{self.user} — {self.topic} — {self.best_score}%'
