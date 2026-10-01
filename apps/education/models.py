"""Education models — content hierarchy.

Subject -> Course -> Module -> Topic -> Lesson
Each Lesson carries its own 10-question test bank (see apps.exam).
"""
from django.db import models

from apps.core.models import ActivatableModel, OrderedModel, TimeStampedModel


class Subject(TimeStampedModel, ActivatableModel):
    name = models.CharField(max_length=150, unique=True, verbose_name='nomi')
    description = models.TextField(blank=True, verbose_name='tavsif')

    class Meta:
        verbose_name = 'Fan'
        verbose_name_plural = 'Fanlar'
        ordering = ['name']

    def __str__(self):
        return self.name


class Course(TimeStampedModel, ActivatableModel, OrderedModel):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='courses', verbose_name='fan')
    title = models.CharField(max_length=200, verbose_name='nomi')
    description = models.TextField(blank=True, verbose_name='tavsif')

    class Meta(OrderedModel.Meta):
        abstract = False
        verbose_name = 'Kurs'
        verbose_name_plural = 'Kurslar'

    def __str__(self):
        return f'{self.subject.name} — {self.title}'


class Module(TimeStampedModel, ActivatableModel, OrderedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules', verbose_name='kurs')
    title = models.CharField(max_length=200, verbose_name='nomi')
    description = models.TextField(blank=True, verbose_name='tavsif')

    class Meta(OrderedModel.Meta):
        abstract = False
        verbose_name = 'Modul'
        verbose_name_plural = 'Modullar'

    def __str__(self):
        return f'{self.course.title} — {self.title}'


class Topic(TimeStampedModel, ActivatableModel, OrderedModel):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='topics', verbose_name='modul')
    title = models.CharField(max_length=200, verbose_name='nomi')
    description = models.TextField(blank=True, verbose_name='tavsif')

    class Meta(OrderedModel.Meta):
        abstract = False
        verbose_name = 'Mavzu'
        verbose_name_plural = 'Mavzular'

    def __str__(self):
        return f'{self.module.title} — {self.title}'


class Lesson(TimeStampedModel, ActivatableModel, OrderedModel):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='lessons', verbose_name='mavzu')
    title = models.CharField(max_length=200, verbose_name='nomi')
    description = models.TextField(blank=True, verbose_name='tavsif')
    video = models.FileField(upload_to='videos/', verbose_name='video fayl')
    duration_minutes = models.PositiveIntegerField(default=0, verbose_name='davomiyligi (daqiqa)')
    is_free_preview = models.BooleanField(
        default=False, verbose_name='bepul sinov darsi',
        help_text='Belgilangan dars botda bepul ochiladi.',
    )
    created_by = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_lessons', verbose_name='kim yaratgan',
    )

    class Meta(OrderedModel.Meta):
        abstract = False
        verbose_name = 'Video dars'
        verbose_name_plural = 'Video darslar'

    def __str__(self):
        return f'{self.topic.title} — {self.title}'
