"""Exam services — per-lesson 10-question test engine.

Same scoring formula and flow as the original xyz platform: select 10
random active/valid questions, shuffle answer order, score on submit,
save an ExamAttempt + per-question breakdown, then roll the result up
into TopicProgress.
"""
import random
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction

from apps.core.utils import get_logger

from .constants import DEFAULT_PASSING_SCORE, QUESTIONS_PER_LESSON
from .models import Answer, ExamAttempt, ExamAttemptQuestion, ExamSettings, Question

logger = get_logger('exam')


def get_passing_score(lesson):
    settings_obj, _ = ExamSettings.objects.get_or_create(
        topic=lesson.topic, defaults={'passing_score': DEFAULT_PASSING_SCORE},
    )
    return settings_obj.passing_score


def lesson_question_bank_ready(lesson):
    questions = Question.objects.filter(lesson=lesson, is_active=True).prefetch_related('answers')
    valid = [q for q in questions if q.has_valid_answers]
    return len(valid) >= QUESTIONS_PER_LESSON, len(valid)


def select_questions_for_lesson(lesson):
    """Shu video uchun 10 ta savolni random tartibda tanlaydi."""
    questions = list(Question.objects.filter(lesson=lesson, is_active=True).prefetch_related('answers'))
    valid = [q for q in questions if q.has_valid_answers]
    if len(valid) < QUESTIONS_PER_LESSON:
        return []
    chosen = random.sample(valid, QUESTIONS_PER_LESSON)
    random.shuffle(chosen)
    return chosen


def build_session_payload(questions):
    payload = []
    for question in questions:
        answer_ids = list(question.answers.values_list('id', flat=True))
        random.shuffle(answer_ids)
        payload.append({'question_id': question.id, 'answer_order': answer_ids})
    return payload


def calculate_result(session_payload, submitted_answers, lesson):
    total = len(session_payload)
    correct = 0
    attempt_question_rows = []

    for order, entry in enumerate(session_payload, start=1):
        question_id = entry['question_id']
        selected_answer_id = submitted_answers.get(str(question_id))

        is_correct = False
        if selected_answer_id:
            is_correct = Answer.objects.filter(
                id=selected_answer_id, question_id=question_id, is_correct=True
            ).exists()
        if is_correct:
            correct += 1

        attempt_question_rows.append({
            'question_id': question_id,
            'selected_answer_id': selected_answer_id or None,
            'is_correct': is_correct,
            'order': order,
        })

    wrong = total - correct
    score = Decimal(0)
    if total > 0:
        score = (Decimal(correct) / Decimal(total) * Decimal(100)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

    passing_score = get_passing_score(lesson)
    is_passed = score >= passing_score

    summary = {
        'total_questions': total,
        'correct_answers': correct,
        'wrong_answers': wrong,
        'score': score,
        'is_passed': is_passed,
        'passing_score': passing_score,
    }
    return summary, attempt_question_rows


@transaction.atomic
def save_attempt(user, lesson, summary, attempt_question_rows, duration_seconds):
    attempt = ExamAttempt.objects.create(
        user=user,
        lesson=lesson,
        topic=lesson.topic,
        total_questions=summary['total_questions'],
        correct_answers=summary['correct_answers'],
        wrong_answers=summary['wrong_answers'],
        score=summary['score'],
        is_passed=summary['is_passed'],
        duration_seconds=duration_seconds,
    )
    ExamAttemptQuestion.objects.bulk_create([
        ExamAttemptQuestion(attempt=attempt, **row) for row in attempt_question_rows
    ])
    logger.info(
        'EXAM_COMPLETED: user=%s lesson=%s score=%s passed=%s',
        user.username, lesson.title, summary['score'], summary['is_passed'],
    )

    from apps.progress.services import update_topic_progress_from_lesson_exam
    update_topic_progress_from_lesson_exam(
        user=user, lesson=lesson, score=summary['score'], passed=summary['is_passed']
    )
    return attempt
