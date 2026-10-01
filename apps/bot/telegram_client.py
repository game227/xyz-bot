"""Raw Telegram Bot API HTTP calls — synchronous, used both from Django
code (apps.live.services broadcast) and wrapped for async bot handlers.
Never raises: a Telegram outage must not break the caller.
"""
import requests
from django.conf import settings

from apps.core.utils import get_logger

API_BASE = 'https://api.telegram.org'
TIMEOUT_SECONDS = 5

logger = get_logger('bot')


def send_message(chat_id, text, *, disable_web_page_preview=False):
    """Fire-and-forget sendMessage. Returns True/False, never raises."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return False
    url = f'{API_BASE}/bot{token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': disable_web_page_preview,
    }
    try:
        resp = requests.post(url, json=payload, timeout=TIMEOUT_SECONDS)
    except requests.RequestException:
        logger.warning('TELEGRAM_SEND_FAILED: chat_id=%s (network error)', chat_id)
        return False

    if resp.status_code == 403:
        _mark_blocked(chat_id)
        return False
    if not resp.ok:
        logger.warning('TELEGRAM_SEND_FAILED: chat_id=%s status=%s body=%s', chat_id, resp.status_code, resp.text[:200])
    return resp.ok


def notify_admins(text):
    """TEACHER/ADMIN sifatida bog'langan barcha akkauntlarga + .env'dagi
    ADMIN_TELEGRAM_IDS'ga xabar yuboradi (yangi support savoli, bot xatosi kabi)."""
    from apps.accounts.models import CustomUser

    ids = set(settings.ADMIN_TELEGRAM_IDS)
    ids.update(
        CustomUser.objects.filter(
            role__in=[CustomUser.Role.ADMIN, CustomUser.Role.TEACHER],
            telegram_id__isnull=False, telegram_blocked=False,
        ).values_list('telegram_id', flat=True)
    )
    sent = 0
    for chat_id in ids:
        if send_message(chat_id, text):
            sent += 1
    return sent


def broadcast_message(text, *, exclude_user_id=None):
    """Barcha faol, botga ulangan foydalanuvchilarga xabar yuboradi (masalan jonli efir boshlanganda)."""
    from apps.accounts.models import CustomUser

    qs = CustomUser.objects.filter(is_active=True, telegram_id__isnull=False, telegram_blocked=False)
    if exclude_user_id:
        qs = qs.exclude(pk=exclude_user_id)
    sent = 0
    for chat_id in qs.values_list('telegram_id', flat=True):
        if send_message(chat_id, text):
            sent += 1
    logger.info('TELEGRAM_BROADCAST: sent=%s', sent)
    return sent


def _mark_blocked(chat_id):
    from apps.accounts.models import CustomUser

    CustomUser.objects.filter(telegram_id=chat_id).update(telegram_blocked=True)
    logger.info('TELEGRAM_USER_BLOCKED: chat_id=%s', chat_id)
