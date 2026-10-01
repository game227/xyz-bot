from django.contrib import admin

from .models import Subscription, SubscriptionPricing, SubscriptionRequest


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_date', 'end_date', 'status')
    list_filter = ('status',)
    search_fields = ('user__username',)


@admin.register(SubscriptionPricing)
class SubscriptionPricingAdmin(admin.ModelAdmin):
    list_display = ('title', 'price_uzs', 'duration_days', 'is_active', 'order')


@admin.register(SubscriptionRequest)
class SubscriptionRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_days', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__username',)
