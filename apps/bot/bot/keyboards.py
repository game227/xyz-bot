from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from . import texts


def phone_request_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=texts.SHARE_PHONE_BTN, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def remove_kb():
    return ReplyKeyboardRemove()


def main_menu_kb(*, is_staff=False):
    rows = [
        [KeyboardButton(text=texts.BTN_SUBJECTS), KeyboardButton(text=texts.BTN_PROGRESS)],
        [KeyboardButton(text=texts.BTN_SUBSCRIPTION), KeyboardButton(text=texts.BTN_LIVE)],
        [KeyboardButton(text=texts.BTN_SUPPORT)],
    ]
    if is_staff:
        rows.append([KeyboardButton(text=texts.BTN_ADMIN)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def list_kb(items, *, prefix, back_callback=None):
    """items: list of (id, label). Renders one button per row + optional back."""
    rows = [[InlineKeyboardButton(text=label, callback_data=f'{prefix}:{item_id}')] for item_id, label in items]
    if back_callback:
        rows.append([InlineKeyboardButton(text=texts.BTN_BACK, callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def lesson_detail_kb(lesson_id, *, can_finish, can_quiz, locked, back_callback):
    rows = []
    if locked:
        rows.append([InlineKeyboardButton(text=texts.GET_SUBSCRIPTION_BTN, callback_data='sub_request')])
    else:
        if can_finish:
            rows.append([InlineKeyboardButton(text=texts.LESSON_FINISH_BTN, callback_data=f'finish:{lesson_id}')])
        if can_quiz:
            rows.append([InlineKeyboardButton(text=texts.LESSON_START_QUIZ_BTN, callback_data=f'quiz:{lesson_id}')])
    rows.append([InlineKeyboardButton(text=texts.BTN_BACK, callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def quiz_answers_kb(question_id, answer_order, answer_texts):
    rows = [
        [InlineKeyboardButton(text=answer_texts.get(aid, '...'), callback_data=f'ans:{question_id}:{aid}')]
        for aid in answer_order
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def subscription_kb(*, has_active):
    rows = [[InlineKeyboardButton(text=texts.SUB_REQUEST_BTN, callback_data='sub_request')]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def plan_choice_kb(plans):
    rows = [
        [InlineKeyboardButton(text=f'{p.title} — {p.price_label}', callback_data=f'plan:{i}')]
        for i, p in enumerate(plans)
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=texts.ADMIN_CONTENT_BTN, callback_data='cm_subj')],
        [InlineKeyboardButton(text=texts.ADMIN_REQ_BTN, callback_data='admin_requests')],
        [InlineKeyboardButton(text=texts.ADMIN_PRICING_BTN, callback_data='admin_pricing')],
        [InlineKeyboardButton(text=texts.ADMIN_LIVE_BTN, callback_data='admin_live')],
        [InlineKeyboardButton(text=texts.ADMIN_SUPPORT_BTN, callback_data='admin_support')],
        [InlineKeyboardButton(text=texts.ADMIN_STAFF_BTN, callback_data='admin_staff')],
        [InlineKeyboardButton(text=texts.ADMIN_USERS_BTN, callback_data='admin_users')],
    ])


# --- kontent boshqaruvi: umumiy yordamchilar ---

def cm_list_kb(items, *, prefix, add_callback=None, back_callback=None):
    """items: [(id, label)]. Har birini bosish item ochadi; pastda +Qo'shish/Orqaga."""
    rows = [[InlineKeyboardButton(text=label, callback_data=f'{prefix}:{item_id}')] for item_id, label in items]
    if add_callback:
        rows.append([InlineKeyboardButton(text=texts.CM_ADD_BTN, callback_data=add_callback)])
    if back_callback:
        rows.append([InlineKeyboardButton(text=texts.BTN_BACK, callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cm_detail_kb(*, open_cb=None, open_label=None, exam_cb=None, toggle_cb=None,
                  toggle_label=None, rename_cb=None, delete_cb=None, back_cb=None):
    rows = []
    if open_cb:
        rows.append([InlineKeyboardButton(text=open_label, callback_data=open_cb)])
    if exam_cb:
        rows.append([InlineKeyboardButton(text=texts.CM_TOPIC_DETAIL_BTN_EXAM, callback_data=exam_cb)])
    if toggle_cb:
        rows.append([InlineKeyboardButton(text=toggle_label or texts.CM_TOGGLE_BTN, callback_data=toggle_cb)])
    if rename_cb:
        rows.append([InlineKeyboardButton(text=texts.CM_RENAME_BTN, callback_data=rename_cb)])
    if delete_cb:
        rows.append([InlineKeyboardButton(text=texts.CM_DELETE_BTN, callback_data=delete_cb)])
    if back_cb:
        rows.append([InlineKeyboardButton(text=texts.BTN_BACK, callback_data=back_cb)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_delete_kb(yes_cb, no_cb):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=texts.CM_DELETE_YES, callback_data=yes_cb),
        InlineKeyboardButton(text=texts.CM_DELETE_NO, callback_data=no_cb),
    ]])


def yes_no_kb(yes_cb, no_cb):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=texts.CM_YES, callback_data=yes_cb),
        InlineKeyboardButton(text=texts.CM_NO, callback_data=no_cb),
    ]])


def correct_answer_choice_kb(answer_texts):
    rows = [
        [InlineKeyboardButton(text=f'{i + 1}. {t[:40]}', callback_data=f'q_correct:{i}')]
        for i, t in enumerate(answer_texts)
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def pricing_detail_kb(pk):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=texts.CM_TOGGLE_BTN, callback_data=f'price_toggle:{pk}')],
        [InlineKeyboardButton(text=texts.CM_DELETE_BTN, callback_data=f'price_del:{pk}')],
        [InlineKeyboardButton(text=texts.BTN_BACK, callback_data='admin_pricing')],
    ])


def role_choice_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=texts.STAFF_ROLE_TEACHER_BTN, callback_data=f'role_set:{user_id}:TEACHER')],
        [InlineKeyboardButton(text=texts.STAFF_ROLE_ADMIN_BTN, callback_data=f'role_set:{user_id}:ADMIN')],
        [InlineKeyboardButton(text=texts.STAFF_ROLE_STUDENT_BTN, callback_data=f'role_set:{user_id}:STUDENT')],
    ])


def user_detail_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=texts.USER_GIVE_SUB_BTN, callback_data=f'user_sub:{user_id}')],
        [InlineKeyboardButton(text=texts.USER_TOGGLE_ACTIVE_BTN, callback_data=f'user_toggle:{user_id}')],
        [InlineKeyboardButton(text=texts.USER_RENAME_BTN, callback_data=f'user_rename:{user_id}')],
        [InlineKeyboardButton(text=texts.BTN_BACK, callback_data='admin_users')],
    ])


def staff_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=texts.STAFF_LIST_BTN, callback_data='staff_list')],
        [InlineKeyboardButton(text=texts.STAFF_ASSIGN_BTN, callback_data='staff_assign')],
        [InlineKeyboardButton(text=texts.BTN_BACK, callback_data='admin_back')],
    ])


def support_reply_kb(message_id):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=texts.ADMIN_SUPPORT_REPLY_BTN, callback_data=f'sup_reply:{message_id}')
    ]])


def request_action_kb(req_id):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=texts.ADMIN_REQ_APPROVE_BTN, callback_data=f'sr_ok:{req_id}'),
        InlineKeyboardButton(text=texts.ADMIN_REQ_REJECT_BTN, callback_data=f'sr_no:{req_id}'),
    ]])


def live_control_kb(*, has_session, session_id=None):
    if has_session:
        return InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text='Efirni tugatish', callback_data=f'live_end:{session_id}')
        ]])
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text='Efir boshlash', callback_data='live_start')
    ]])


def platform_choice_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text='YouTube', callback_data='platform:YOUTUBE'),
        InlineKeyboardButton(text='Telegram', callback_data='platform:TELEGRAM'),
    ]])
