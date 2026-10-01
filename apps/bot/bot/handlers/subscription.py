from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from .. import keyboards, services_bridge as services, texts
from ..common import require_registration
from ..states import SubscriptionRequestFlow

router = Router(name='subscription')


@router.message(F.text == texts.BTN_SUBSCRIPTION)
async def show_subscription(message: Message, db_user=None):
    if not await require_registration(message, db_user):
        return
    sub = await services.get_active_subscription(db_user)
    lines = [texts.SUB_TITLE]
    if sub and sub.is_currently_active():
        lines.append(texts.SUB_ACTIVE.format(end_date=sub.end_date.strftime('%d.%m.%Y')))
    else:
        lines.append(texts.SUB_NONE)

    plans = await services.get_subscription_plans()
    if plans:
        lines.append(texts.SUB_PLANS_TITLE)
        for p in plans:
            lines.append(texts.SUB_PLAN_ROW.format(title=p.title, price=p.price_label, days=p.duration_days))

    await message.answer(
        '\n'.join(lines),
        reply_markup=keyboards.subscription_kb(has_active=bool(sub and sub.is_currently_active())),
    )


@router.callback_query(F.data == 'sub_request')
async def start_subscription_request(callback: CallbackQuery, state: FSMContext):
    plans = await services.get_subscription_plans()
    if not plans:
        await callback.answer('Tariflar hozircha mavjud emas.', show_alert=True)
        return
    await state.set_state(SubscriptionRequestFlow.choosing_plan)
    await callback.answer()
    await callback.message.answer(texts.SUB_REQUEST_ASK_PLAN, reply_markup=keyboards.plan_choice_kb(plans))


@router.callback_query(SubscriptionRequestFlow.choosing_plan, F.data.startswith('plan:'))
async def choose_plan(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data.split(':')[1])
    plan = await services.get_plan_by_index(idx)
    if not plan:
        await callback.answer('Topilmadi', show_alert=True)
        return
    await state.update_data(plan_days=plan.duration_days)
    await state.set_state(SubscriptionRequestFlow.note)
    await callback.answer()
    await callback.message.answer(texts.SUB_REQUEST_ASK_NOTE)


@router.message(SubscriptionRequestFlow.note, F.text)
async def submit_request(message: Message, state: FSMContext, db_user=None):
    data = await state.get_data()
    note = message.text.strip()
    if note.lower() in {'yo\'q', 'yoq', 'yo`q'}:
        note = ''
    await services.create_subscription_request(user=db_user, plan_days=data['plan_days'], note=note)
    await state.clear()
    await message.answer(texts.SUB_REQUEST_SENT)
