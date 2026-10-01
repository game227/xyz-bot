"""Subscription services."""
import datetime

from django.utils import timezone

from apps.core.utils import get_logger

from .models import Subscription, SubscriptionPricing, SubscriptionRequest

logger = get_logger('subscription')

DEFAULT_PLANS = [
    {'title': '1 oy', 'days': 30, 'price_uzs': 100000},
    {'title': '3 oy', 'days': 90, 'price_uzs': 250000},
    {'title': '1 yil', 'days': 365, 'price_uzs': 800000},
]


def ensure_default_pricing():
    if SubscriptionPricing.objects.exists():
        return
    for i, plan in enumerate(DEFAULT_PLANS):
        SubscriptionPricing.objects.create(
            title=plan['title'], price_uzs=plan['price_uzs'],
            duration_days=plan['days'], order=i, is_active=True,
        )


def get_subscription_plans():
    ensure_default_pricing()
    return list(SubscriptionPricing.objects.filter(is_active=True).order_by('order', 'duration_days', 'id'))


def get_active_subscription(user):
    subscription = Subscription.objects.filter(user=user).order_by('-end_date').first()
    if subscription:
        subscription.refresh_status()
    return subscription


def has_active_subscription(user):
    subscription = get_active_subscription(user)
    return bool(subscription and subscription.is_currently_active())


def activate_subscription(user, duration_days, activated_by):
    """Admin/o'qituvchi amali: mavjud faol muddatni uzaytiradi yoki yangi obuna ochadi."""
    today = timezone.localdate()
    current = (
        Subscription.objects.filter(user=user, status=Subscription.Status.ACTIVE)
        .order_by('-end_date').first()
    )
    if current:
        current.refresh_status()
        if current.is_currently_active():
            start_date = current.start_date
            end_date = current.end_date + datetime.timedelta(days=duration_days)
            current.end_date = end_date
            current.duration_days = (end_date - start_date).days
            current.activated_by = activated_by
            current.save(update_fields=['end_date', 'duration_days', 'activated_by', 'updated_at'])
            logger.info('SUBSCRIPTION_EXTENDED: user=%s +%s days -> %s', user.username, duration_days, end_date)
            return current

    start_date = today
    end_date = start_date + datetime.timedelta(days=duration_days)
    subscription = Subscription.objects.create(
        user=user, start_date=start_date, end_date=end_date,
        duration_days=duration_days, status=Subscription.Status.ACTIVE, activated_by=activated_by,
    )
    logger.info('SUBSCRIPTION_ACTIVATED: user=%s days=%s', user.username, duration_days)
    return subscription


def create_subscription_request(*, user, plan_days, note=''):
    req = SubscriptionRequest.objects.create(user=user, plan_days=plan_days, note=note)
    logger.info('SUBSCRIPTION_REQUEST: user=%s plan=%s', user.username, plan_days)
    return req
