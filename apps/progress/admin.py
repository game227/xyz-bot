from django.contrib import admin

from .models import LessonProgress, TopicProgress


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'is_completed', 'completed_at')
    list_filter = ('is_completed',)
    search_fields = ('user__username',)


@admin.register(TopicProgress)
class TopicProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'topic', 'best_score', 'is_completed')
    list_filter = ('is_completed',)
    search_fields = ('user__username',)
