from django.contrib import admin

from .models import Course, Lesson, Module, Subject, Topic


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    search_fields = ('name',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'order', 'is_active')
    list_filter = ('subject', 'is_active')
    search_fields = ('title',)


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'is_active')
    list_filter = ('course', 'is_active')
    search_fields = ('title',)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'order', 'is_active')
    list_filter = ('module', 'is_active')
    search_fields = ('title',)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'is_free_preview', 'order', 'is_active')
    list_filter = ('topic', 'is_free_preview', 'is_active')
    search_fields = ('title',)
