from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from django.utils import timezone

from .. import keyboards, services_bridge as services, texts
from ..states import QuizFlow

router = Router(name='quiz')


@router.callback_query(F.data.startswith('quiz:'))
async def start_quiz(callback: CallbackQuery, state: FSMContext, db_user=None):
    lesson_id = int(callback.data.split(':')[1])
    lesson = await services.get_lesson(lesson_id)
    if not lesson:
        await callback.answer('Topilmadi', show_alert=True)
        return

    if not await services.can_start_lesson_exam(db_user, lesson):
        await callback.answer(texts.LESSON_LOCKED_MSG, show_alert=True)
        return

    questions = await services.select_questions_for_lesson(lesson)
    if not questions:
        await callback.answer(texts.QUIZ_NOT_READY, show_alert=True)
        return

    session_payload = await services.build_session_payload(questions)
    question_ids = [q.id for q in questions]
    answer_ids = [aid for entry in session_payload for aid in entry['answer_order']]
    question_texts = await services.get_question_texts(question_ids)
    answer_texts = await services.get_answer_texts(answer_ids)

    await state.set_state(QuizFlow.answering)
    await state.update_data(
        lesson_id=lesson_id,
        session_payload=session_payload,
        question_texts=question_texts,
        answer_texts=answer_texts,
        current_index=0,
        submitted_answers={},
        started_at=timezone.now().isoformat(),
    )
    await callback.answer()
    await _render_question(callback.message, state)


async def _render_question(message, state: FSMContext):
    data = await state.get_data()
    idx = data['current_index']
    total = len(data['session_payload'])
    entry = data['session_payload'][idx]
    question_text = data['question_texts'].get(entry['question_id'], '...')
    header = texts.QUIZ_QUESTION_HEADER.format(current=idx + 1, total=total)
    await message.answer(
        f'{header}\n\n{question_text}',
        reply_markup=keyboards.quiz_answers_kb(
            entry['question_id'], entry['answer_order'], data['answer_texts'],
        ),
    )


@router.callback_query(QuizFlow.answering, F.data.startswith('ans:'))
async def on_answer(callback: CallbackQuery, state: FSMContext, db_user=None):
    _, qid_str, aid_str = callback.data.split(':')
    data = await state.get_data()
    idx = data['current_index']
    entry = data['session_payload'][idx]

    if entry['question_id'] != int(qid_str):
        await callback.answer()
        return

    submitted = data['submitted_answers']
    submitted[qid_str] = int(aid_str)
    idx += 1

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    if idx < len(data['session_payload']):
        await state.update_data(current_index=idx, submitted_answers=submitted)
        await _render_question(callback.message, state)
        return

    lesson = await services.get_lesson(data['lesson_id'])
    summary, rows = await services.calculate_result(data['session_payload'], submitted, lesson)
    started_at = timezone.datetime.fromisoformat(data['started_at'])
    duration_seconds = int((timezone.now() - started_at).total_seconds())
    await services.save_attempt(db_user, lesson, summary, rows, duration_seconds)
    await state.clear()

    verdict = texts.QUIZ_PASSED if summary['is_passed'] else texts.QUIZ_FAILED
    await callback.message.answer(texts.QUIZ_RESULT.format(
        correct=summary['correct_answers'], total=summary['total_questions'],
        score=summary['score'], verdict=verdict,
    ))
