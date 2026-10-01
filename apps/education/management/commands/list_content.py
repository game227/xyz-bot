"""Fan -> Kurs -> Modul -> Mavzu -> Dars ierarxiyasini ID'lari bilan chop etadi
— `add_lesson_video` uchun kerakli topic_id/lesson_id'ni topish uchun.

    python manage.py list_content
"""
from django.core.management.base import BaseCommand

from apps.education.models import Subject


class Command(BaseCommand):
    help = "Butun kontent ierarxiyasini ID'lari bilan ko'rsatadi."

    def handle(self, *args, **options):
        subjects = Subject.objects.prefetch_related(
            'courses__modules__topics__lessons'
        ).order_by('name')
        if not subjects:
            self.stdout.write('Hozircha hech narsa yo\'q.')
            return
        for subject in subjects:
            self.stdout.write(f'[fan {subject.id}] {subject.name}')
            for course in subject.courses.all():
                self.stdout.write(f'  [kurs {course.id}] {course.title}')
                for module in course.modules.all():
                    self.stdout.write(f'    [modul {module.id}] {module.title}')
                    for topic in module.topics.all():
                        self.stdout.write(f'      [mavzu {topic.id}] {topic.title}')
                        for lesson in topic.lessons.all():
                            has_video = 'video bor' if lesson.video else 'VIDEO YO\'Q'
                            self.stdout.write(
                                f'        [dars {lesson.id}] {lesson.title} ({has_video})'
                            )
