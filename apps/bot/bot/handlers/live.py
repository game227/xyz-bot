from aiogram import F, Router
from aiogram.types import Message

from .. import services_bridge as services, texts
from ..common import require_registration

router = Router(name='live')


@router.message(F.text == texts.BTN_LIVE)
async def show_live(message: Message, db_user=None):
    if not await require_registration(message, db_user):
        return
    session = await services.get_current_live_session()
    if not session:
        await message.answer(f'{texts.LIVE_TITLE}\n\n{texts.LIVE_NONE}')
        return
    await message.answer(
        f'{texts.LIVE_TITLE}\n\n' + texts.LIVE_ACTIVE.format(title=session.title, url=session.stream_url)
    )
