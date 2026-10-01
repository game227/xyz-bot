"""Diskdagi mahalliy video faylni darsga biriktiradi — Telegram orqali emas,
to'g'ridan-to'g'ri fayl tizimidan, shuning uchun Bot API'ning ~20MB yuklab
olish chegarasi bu yerda umuman ishlamaydi (faqat disk hajmi bilan cheklangan).

Video faylni oldindan shu kompyuterdagi biror papkaga (masalan
incoming_videos/) joylashtiring, so'ng:

    Yangi dars yaratish:
        python manage.py add_lesson_video <topic_id> incoming_videos/dars1.mp4 --title "1-dars" --duration 15
        python manage.py add_lesson_video <topic_id> incoming_videos/dars1.mp4 --title "1-dars" --duration 15 --free

    Mavjud darsning videosini almashtirish:
        python manage.py add_lesson_video --lesson-id 7 incoming_videos/yangi.mp4

    Mavzu ID'larini ko'rish uchun:
        python manage.py shell -c "from apps.education.models import Topic; [print(t.id, t) for t in Topic.objects.all()]"
"""
import os

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError

from apps.education.models import Lesson, Topic


class Command(BaseCommand):
    help = "Diskdagi video faylni darsga biriktiradi (Telegram/bot orqali emas)."

    def add_arguments(self, parser):
        parser.add_argument('topic_id', type=int, nargs='?', default=None,
                             help='Yangi dars qaysi mavzuga qo\'shilsin')
        parser.add_argument('video_path', type=str, help='Video faylning shu kompyuterdagi manzili')
        parser.add_argument('--title', default=None, help='Dars nomi (yangi dars uchun shart)')
        parser.add_argument('--duration', type=int, default=0, help='Davomiyligi (daqiqa)')
        parser.add_argument('--free', action='store_true', help="Bepul sinov darsi qilib belgilash")
        parser.add_argument('--lesson-id', type=int, default=None,
                             help="Berilsa, yangi dars yaratish o'rniga shu darsning videosi almashtiriladi")

    def handle(self, *args, **options):
        video_path = options['video_path']
        if not os.path.isfile(video_path):
            raise CommandError(f"Fayl topilmadi: {video_path}")
        filename = os.path.basename(video_path)
        size_mb = os.path.getsize(video_path) / (1024 * 1024)

        if options['lesson_id']:
            lesson = Lesson.objects.filter(pk=options['lesson_id']).first()
            if not lesson:
                raise CommandError(f"Dars topilmadi: id={options['lesson_id']}")
            with open(video_path, 'rb') as f:
                lesson.video.save(filename, File(f), save=True)
            self.stdout.write(self.style.SUCCESS(
                f"Dars #{lesson.id} '{lesson.title}' videosi yangilandi: {filename} ({size_mb:.1f} MB)"
            ))
            return

        if not options['topic_id']:
            raise CommandError("Yangi dars uchun topic_id kerak (yoki --lesson-id bilan mavjud darsni yangilang).")
        if not options['title']:
            raise CommandError("Yangi dars uchun --title kerak.")

        topic = Topic.objects.filter(pk=options['topic_id']).first()
        if not topic:
            raise CommandError(f"Mavzu topilmadi: id={options['topic_id']}")

        lesson = Lesson(
            topic=topic, title=options['title'], duration_minutes=options['duration'],
            is_free_preview=options['free'], order=Lesson.objects.filter(topic=topic).count(),
        )
        with open(video_path, 'rb') as f:
            lesson.video.save(filename, File(f), save=False)
        lesson.save()
        self.stdout.write(self.style.SUCCESS(
            f"Dars yaratildi: #{lesson.id} '{lesson.title}' — {filename} ({size_mb:.1f} MB), mavzu: {topic.title}"
        ))
