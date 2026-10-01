from django.contrib import admin

from .models import Answer, ExamAttempt, ExamSettings, Question


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'lesson', 'is_active')
    list_filter = ('lesson', 'is_active')
    search_fields = ('text',)
    inlines = [AnswerInline]


@admin.register(ExamSettings)
class ExamSettingsAdmin(admin.ModelAdmin):
    list_display = ('topic', 'passing_score')


@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'score', 'is_passed', 'created_at')
    list_filter = ('is_passed', 'lesson')
    search_fields = ('user__username',)
    readonly_fields = [f.name for f in ExamAttempt._meta.fields]
