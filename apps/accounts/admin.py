from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'get_full_name', 'role', 'phone_number', 'telegram_id', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'phone_number', 'telegram_id', 'telegram_username')
    fieldsets = UserAdmin.fieldsets + (
        ('Qo‘shimcha', {'fields': ('role', 'phone_number', 'telegram_id', 'telegram_username')}),
    )
