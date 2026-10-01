from django import forms
from django.forms import inlineformset_factory

from apps.education.models import Course, Lesson, Module, Subject, Topic
from apps.exam.models import Answer, ExamSettings, Question
from apps.live.models import LiveSession
from apps.notifications.models import SupportMessage


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'description', 'is_active']


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['subject', 'title', 'description', 'order', 'is_active']


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['course', 'title', 'description', 'order', 'is_active']


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['module', 'title', 'description', 'order', 'is_active']


class ExamSettingsForm(forms.ModelForm):
    class Meta:
        model = ExamSettings
        fields = ['passing_score']


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['topic', 'title', 'description', 'video', 'duration_minutes', 'is_free_preview', 'order', 'is_active']


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['lesson', 'text', 'explanation', 'is_active']


AnswerFormSet = inlineformset_factory(
    Question, Answer,
    fields=['text', 'is_correct', 'order'],
    extra=4, max_num=6, can_delete=True,
)


class LiveSessionForm(forms.ModelForm):
    class Meta:
        model = LiveSession
        fields = ['title', 'platform', 'stream_url']


class SupportReplyForm(forms.ModelForm):
    class Meta:
        model = SupportMessage
        fields = ['admin_reply']
        widgets = {'admin_reply': forms.Textarea(attrs={'rows': 4})}
        labels = {'admin_reply': 'Javob'}
