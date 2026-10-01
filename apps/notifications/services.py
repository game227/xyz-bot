"""Support (savol-javob) va eslatma xizmatlari.

Eslatmalar `manage.py send_reminders` orqali (masalan kunlik cron/systemd
timer bilan) chaqiriladi — bu yerda faqat kimga, qachon yuborilganini
aniqlab, ReminderLog bilan bir kunda ikki marta yubormaslikni kafolatlaydi.
"""
import datetime

from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone

from apps.core.utils import get_logger
from apps.progress.models import LessonProgress
from apps.subscription.models import Subscription

from .models import ReminderLog, SupportMessage

logger = get_logger('notifications')

SUBSCRIPTION_REMINDER_DAYS_BEFORE = 3
INACTIVITY_REMINDER_AFTER_DAYS = 7


# ---------------------------------------------------------------------------
# Support (bot orqali savol yuborish)
# ---------------------------------------------------------------------------

def create_support_message(user, text):
    from apps.bot.telegram_client import notify_admins

    msg = SupportMessage.objects.create(user=user, message=text.strip()[:2000])
    label = user.get_full_name() or user.username
    notify_admins(
        f'<b>Yangi savol</b>\n{label} ({user.phone_number or "—"}):\n\n{msg.message}\n\n'
        f'Javob berish: Boshqaruv → Savollar.'
    )
    logger.info('SUPPORT_MESSAGE_CREATED: user=%s id=%s', user.username, msg.id)
    return msg


def list_support_messages(*, only_unanswered=False):
    qs = SupportMessage.objects.select_related('user').order_by('-created_at')
    if only_unanswered:
        qs = qs.filter(is_answered=False)
    return list(qs)


def get_support_message(pk):
    return SupportMessage.objects.select_related('user').filter(pk=pk).first()


def answer_support_message(pk, admin_user, reply_text):
    from apps.bot.telegram_client import send_message

    msg = SupportMessage.objects.select_related('user').filter(pk=pk).first()
    if not msg:
        return None
    msg.admin_reply = reply_text.strip()[:2000]
    msg.is_answered = True
    msg.answered_by = admin_user
    msg.answered_at = timezone.now()
    msg.save(update_fields=['admin_reply', 'is_answered', 'answered_by', 'answered_at', 'updated_at'])

    if msg.user.telegram_id and not msg.user.telegram_blocked:
        send_message(
            msg.user.telegram_id,
            f'<b>Savolingizga javob keldi:</b>\n\n'
            f'Savol: {msg.message}\n\n'
            f'Javob: {msg.admin_reply}',
        )
    logger.info('SUPPORT_MESSAGE_ANSWERED: id=%s by=%s', msg.id, admin_user.username)
    return msg


# ---------------------------------------------------------------------------
# Eslatmalar
# ---------------------------------------------------------------------------

def _log_reminder(user, kind, sent_date):
    """True — birinchi marta yuborildi (log yozildi); False — bugun allaqachon yuborilgan."""
    try:
        ReminderLog.objects.create(user=user, kind=kind, sent_date=sent_date)
        return True
    except IntegrityError:
        return False


def send_subscription_expiry_reminders():
    from apps.bot.telegram_client import send_message

    today = timezone.localdate()
    horizon = today + datetime.timedelta(days=SUBSCRIPTION_REMINDER_DAYS_BEFORE)
    qs = (
        Subscription.objects.filter(status=Subscription.Status.ACTIVE, end_date__gte=today, end_date__lte=horizon)
        .select_related('user')
    )
    sent = 0
    for sub in qs:
        user = sub.user
        if not user.telegram_id or user.telegram_blocked:
            continue
        if not _log_reminder(user, ReminderLog.Kind.SUBSCRIPTION_EXPIRY, today):
            continue
        days_left = (sub.end_date - today).days
        text = (
            f'Obunangiz {days_left} kundan so‘ng ({sub.end_date}) tugaydi. '
            f'Uzaytirish uchun "Obuna" bo‘limidan so‘rov yuboring.'
        )
        if send_message(user.telegram_id, text):
            sent += 1
    logger.info('SUBSCRIPTION_EXPIRY_REMINDERS: sent=%s', sent)
    return sent


def send_inactivity_reminders():
    from apps.bot.telegram_client import send_message

    from apps.accounts.models import CustomUser

    today = timezone.localdate()
    threshold = timezone.now() - datetime.timedelta(days=INACTIVITY_REMINDER_AFTER_DAYS)
    active_ids = set(
        Subscription.objects.filter(status=Subscription.Status.ACTIVE, end_date__gte=today)
        .values_list('user_id', flat=True)
    )
    if not active_ids:
        return 0

    recent_progress_ids = set(
        LessonProgress.objects.filter(user_id__in=active_ids, updated_at__gte=threshold)
        .values_list('user_id', flat=True)
    )
    stale_ids = active_ids - recent_progress_ids

    sent = 0
    for user in CustomUser.objects.filter(id__in=stale_ids, telegram_id__isnull=False, telegram_blocked=False):
        if not _log_reminder(user, ReminderLog.Kind.INACTIVITY, today):
            continue
        text = (
            'Bir muncha vaqtdan beri darslarga qaytmadingiz! '
            'Bilimingizni yangilash uchun botga qayting va davom eting.'
        )
        if send_message(user.telegram_id, text):
            sent += 1
    logger.info('INACTIVITY_REMINDERS: sent=%s', sent)
    return sent
