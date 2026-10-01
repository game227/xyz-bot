from django.contrib import admin

from .models import ReminderLog, SupportMessage


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_answered', 'answered_by', 'created_at')
    list_filter = ('is_answered',)
    search_fields = ('user__username', 'message')


@admin.register(ReminderLog)
class ReminderLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'kind', 'sent_date')
    list_filter = ('kind', 'sent_date')
    search_fields = ('user__username',)
