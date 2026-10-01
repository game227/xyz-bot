from django.contrib import admin

from .models import LiveSession


@admin.register(LiveSession)
class LiveSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'host', 'platform', 'status', 'started_at', 'ended_at')
    list_filter = ('status', 'platform')
    search_fields = ('title', 'host__username')
