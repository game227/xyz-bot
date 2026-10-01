from aiogram import F, Router
from aiogram.types import Message

from .. import services_bridge as services, texts
from ..common import require_registration

router = Router(name='progress')


@router.message(F.text == texts.BTN_PROGRESS)
async def show_progress(message: Message, db_user=None):
    if not await require_registration(message, db_user):
        return
    summary = await services.get_dashboard_summary(db_user)

    lines = [
        texts.PROGRESS_TITLE,
        texts.PROGRESS_OVERALL.format(percent=summary['overall_progress']),
        texts.PROGRESS_TOPICS.format(count=summary['completed_topics_count']),
    ]

    attempts = summary['recent_attempts']
    if attempts:
        lines.append(texts.PROGRESS_RECENT)
        for a in attempts:
            lines.append(texts.PROGRESS_ATTEMPT_ROW.format(
                lesson=a.lesson.title, score=a.score, date=a.created_at.strftime('%d.%m.%Y'),
            ))
    else:
        lines.append(texts.PROGRESS_NO_ATTEMPTS)

    await message.answer('\n'.join(lines))
