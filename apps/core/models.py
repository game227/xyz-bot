"""Shared abstract base models used across every app."""
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='yaratilgan sana')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='yangilangan sana')

    class Meta:
        abstract = True


class ActivatableModel(models.Model):
    is_active = models.BooleanField(default=True, verbose_name='faol')

    class Meta:
        abstract = True


class OrderedModel(models.Model):
    order = models.PositiveIntegerField(default=0, verbose_name='tartib')

    class Meta:
        abstract = True
        ordering = ['order']
