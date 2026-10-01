from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    full_name = State()
    phone = State()


class QuizFlow(StatesGroup):
    answering = State()


class SubscriptionRequestFlow(StatesGroup):
    choosing_plan = State()
    note = State()


class AdminLiveStart(StatesGroup):
    title = State()
    platform = State()
    url = State()


class SupportFlow(StatesGroup):
    message = State()


class AdminSupportReply(StatesGroup):
    text = State()


class ContentFlow(StatesGroup):
    text_input = State()      # generic single-value text capture; data['kind'] tanlaydi
    lesson_video = State()
    lesson_duration = State()
    question_answer = State()
    exam_score = State()
    pricing_price = State()
    pricing_days = State()


class StaffFlow(StatesGroup):
    identifier = State()


class UserFlow(StatesGroup):
    subscription_days = State()
    rename = State()
