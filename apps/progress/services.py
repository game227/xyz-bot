"""Progress services.

The bot has no video player, so "watched" is a simple explicit action
(a "Darsni tugatdim" button) rather than a tracked watch-percentage —
an intentional MVP simplification.
"""
from django.utils import timezone

from apps.core.utils import get_logger
from apps.education.models import Course, Topic

from .models import LessonProgress, TopicProgress

logger = get_logger('progress')


def mark_lesson_complete(user, lesson):
    progress, _ = LessonProgress.objects.get_or_create(user=user, lesson=lesson)
    if not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = timezone.now()
        progress.save(update_fields=['is_completed', 'completed_at', 'updated_at'])
        logger.info('LESSON_COMPLETED: user=%s lesson=%s', user.username, lesson.title)
    return progress


def all_lessons_completed(user, topic):
    lesson_ids = set(topic.lessons.filter(is_active=True).values_list('id', flat=True))
    if not lesson_ids:
        return False
    completed_ids = set(
        LessonProgress.objects.filter(
            user=user, lesson_id__in=lesson_ids, is_completed=True
        ).values_list('lesson_id', flat=True)
    )
    return lesson_ids.issubset(completed_ids)


def can_start_lesson_exam(user, lesson):
    """Video 'tugatdim' deb belgilangach shu videoning 10 talik testi ochiladi."""
    return LessonProgress.objects.filter(user=user, lesson=lesson, is_completed=True).exists()


def update_topic_progress_from_lesson_exam(user, lesson, score, passed):
    from apps.exam.models import ExamAttempt

    topic = lesson.topic
    progress, _ = TopicProgress.objects.get_or_create(user=user, topic=topic)

    if score > progress.best_score:
        progress.best_score = score

    lesson_ids = list(topic.lessons.filter(is_active=True).values_list('id', flat=True))
    if lesson_ids:
        passed_lesson_ids = set(
            ExamAttempt.objects.filter(
                user=user, lesson_id__in=lesson_ids, is_passed=True
            ).values_list('lesson_id', flat=True)
        )
        all_passed = set(lesson_ids).issubset(passed_lesson_ids)
    else:
        all_passed = False

    if all_passed and not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = timezone.now()
        logger.info('TOPIC_COMPLETED: user=%s topic=%s', user.username, topic.title)

    progress.save(update_fields=['best_score', 'is_completed', 'completed_at', 'updated_at'])
    return progress


def _percent(done, total):
    if total == 0:
        return 0
    return round((done / total) * 100, 1)


def course_progress_percent(user, course):
    topic_ids = list(Topic.objects.filter(module__course=course, is_active=True).values_list('id', flat=True))
    if not topic_ids:
        return 0
    completed = TopicProgress.objects.filter(user=user, topic_id__in=topic_ids, is_completed=True).count()
    return _percent(completed, len(topic_ids))


def overall_progress_percent(user):
    total_topics = Topic.objects.filter(is_active=True).count()
    if total_topics == 0:
        return 0
    completed_topics = TopicProgress.objects.filter(user=user, is_completed=True).count()
    return _percent(completed_topics, total_topics)


def get_dashboard_summary(user):
    """Bot uchun ixcham progress ma'lumoti (grafiklarsiz — matn ko'rinishida)."""
    completed_topics_count = TopicProgress.objects.filter(user=user, is_completed=True).count()
    recent_attempts = list(
        user.exam_attempts.select_related('lesson', 'topic').order_by('-created_at')[:5]
    )
    return {
        'overall_progress': overall_progress_percent(user),
        'completed_topics_count': completed_topics_count,
        'recent_attempts': recent_attempts,
    }
