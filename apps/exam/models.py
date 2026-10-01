"""Exam models — each Lesson has its own 10-question test bank."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import ActivatableModel, OrderedModel, TimeStampedModel
from apps.education.models import Lesson, Topic

from .constants import DEFAULT_PASSING_SCORE, QUESTIONS_PER_LESSON


class Question(TimeStampedModel, ActivatableModel):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='questions', verbose_name='video dars')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='questions', verbose_name='mavzu')
    text = models.TextField(verbose_name='savol matni')
    explanation = models.TextField(blank=True, verbose_name='tushuntirish')

    class Meta:
        verbose_name = 'Savol'
        verbose_name_plural = 'Savollar'
        ordering = ['id']

    def __str__(self):
        return self.text[:60]

    def clean(self):
        super().clean()
        if self.lesson_id:
            active_count = Question.objects.filter(
                lesson_id=self.lesson_id, is_active=True
            ).exclude(pk=self.pk).count()
            if self.is_active and active_count >= QUESTIONS_PER_LESSON:
                raise ValidationError(
                    f'Har bir video uchun maksimal {QUESTIONS_PER_LESSON} ta faol savol bo‘lishi mumkin.'
                )

    def save(self, *args, **kwargs):
        if self.lesson_id:
            self.topic_id = self.lesson.topic_id
        super().save(*args, **kwargs)

    @property
    def has_valid_answers(self):
        return self.answers.count() >= 4 and self.answers.filter(is_correct=True).count() == 1


class Answer(TimeStampedModel, OrderedModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers', verbose_name='savol')
    text = models.CharField(max_length=500, verbose_name='javob matni')
    is_correct = models.BooleanField(default=False, verbose_name="to'g'ri javobmi")

    class Meta(OrderedModel.Meta):
        abstract = False
        verbose_name = 'Javob'
        verbose_name_plural = 'Javoblar'

    def __str__(self):
        return f'{self.text} ({"to\'g\'ri" if self.is_correct else "noto\'g\'ri"})'


class ExamSettings(TimeStampedModel):
    topic = models.OneToOneField(Topic, on_delete=models.CASCADE, related_name='exam_settings', verbose_name='mavzu')
    passing_score = models.PositiveIntegerField(default=DEFAULT_PASSING_SCORE, verbose_name="o'tish foizi (%)")

    class Meta:
        verbose_name = 'Test sozlamasi'
        verbose_name_plural = 'Test sozlamalari'

    def __str__(self):
        return f'{self.topic.title} sozlamasi'


class ExamAttempt(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='exam_attempts', verbose_name='foydalanuvchi',
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='exam_attempts', verbose_name='video dars')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='exam_attempts', verbose_name='mavzu')
    total_questions = models.PositiveIntegerField(verbose_name='savollar soni')
    correct_answers = models.PositiveIntegerField(verbose_name="to'g'ri javoblar")
    wrong_answers = models.PositiveIntegerField(verbose_name="noto'g'ri javoblar")
    score = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='foiz (%)')
    is_passed = models.BooleanField(default=False, verbose_name="o'tdimi")
    duration_seconds = models.PositiveIntegerField(default=0, verbose_name='sarflangan vaqt (soniya)')

    class Meta:
        verbose_name = 'Test urinishi'
        verbose_name_plural = 'Test urinishlari'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.lesson} — {self.score}%'

    def save(self, *args, **kwargs):
        if self.lesson_id:
            self.topic_id = self.lesson.topic_id
        super().save(*args, **kwargs)


class ExamAttemptQuestion(models.Model):
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='attempt_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='attempt_questions')
    selected_answer = models.ForeignKey(Answer, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Urinish savoli'
        verbose_name_plural = 'Urinish savollari'
        ordering = ['order']

    def __str__(self):
        return f'{self.attempt_id} — {self.question_id}'
