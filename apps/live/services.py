"""Live session services — shared by the bot admin handlers and the web panel
so the start/duplicate-guard logic lives in exactly one place."""
from django.db import transaction

from apps.core.utils import get_logger

from .models import LiveSession

logger = get_logger('live')


def get_current_live_session():
    return LiveSession.objects.filter(status=LiveSession.Status.LIVE).order_by('-started_at').first()


@transaction.atomic
def start_live_session(user, title, platform, stream_url):
    """Returns (session, created). created=False means the host already had
    a live session running (select_for_update guards a double-submit)."""
    existing = (
        LiveSession.objects.select_for_update()
        .filter(host=user, status=LiveSession.Status.LIVE)
        .order_by('-started_at').first()
    )
    if existing:
        return existing, False

    from django.utils import timezone
    session = LiveSession.objects.create(
        title=title, host=user, platform=platform, stream_url=stream_url,
        status=LiveSession.Status.LIVE, started_at=timezone.now(),
    )
    logger.info('LIVE_STARTED: host=%s title=%s', user.username, title)

    from apps.bot.telegram_client import broadcast_message
    broadcast_message(
        exclude_user_id=user.pk,
        text=(
            f'<b>Jonli dars boshlandi: {session.title}</b>\n'
            f'{user.get_full_name() or user.username} jonli dars boshladi.\n\n'
            f'Havola: {session.stream_url}'
        ),
    )
    return session, True
