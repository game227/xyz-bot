from django.urls import path

from . import views

app_name = 'panel'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.DashboardView.as_view(), name='dashboard'),

    path('subjects/', views.SubjectListView.as_view(), name='subject_list'),
    path('subjects/add/', views.SubjectCreateView.as_view(), name='subject_add'),
    path('subjects/<int:pk>/edit/', views.SubjectUpdateView.as_view(), name='subject_edit'),
    path('subjects/<int:pk>/delete/', views.SubjectDeleteView.as_view(), name='subject_delete'),

    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('courses/add/', views.CourseCreateView.as_view(), name='course_add'),
    path('courses/<int:pk>/edit/', views.CourseUpdateView.as_view(), name='course_edit'),
    path('courses/<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),

    path('modules/', views.ModuleListView.as_view(), name='module_list'),
    path('modules/add/', views.ModuleCreateView.as_view(), name='module_add'),
    path('modules/<int:pk>/edit/', views.ModuleUpdateView.as_view(), name='module_edit'),
    path('modules/<int:pk>/delete/', views.ModuleDeleteView.as_view(), name='module_delete'),

    path('topics/', views.TopicListView.as_view(), name='topic_list'),
    path('topics/add/', views.TopicCreateView.as_view(), name='topic_add'),
    path('topics/<int:pk>/edit/', views.TopicUpdateView.as_view(), name='topic_edit'),
    path('topics/<int:pk>/delete/', views.TopicDeleteView.as_view(), name='topic_delete'),
    path('topics/<int:topic_id>/exam-settings/', views.exam_settings_view, name='exam_settings'),

    path('lessons/', views.LessonListView.as_view(), name='lesson_list'),
    path('lessons/add/', views.LessonCreateView.as_view(), name='lesson_add'),
    path('lessons/<int:pk>/edit/', views.LessonUpdateView.as_view(), name='lesson_edit'),
    path('lessons/<int:pk>/delete/', views.LessonDeleteView.as_view(), name='lesson_delete'),

    path('questions/', views.QuestionListView.as_view(), name='question_list'),
    path('questions/add/', views.question_form_view, name='question_add'),
    path('questions/<int:pk>/edit/', views.question_form_view, name='question_edit'),
    path('questions/<int:pk>/delete/', views.QuestionDeleteView.as_view(), name='question_delete'),

    path('subscription-requests/', views.SubscriptionRequestListView.as_view(), name='subscription_requests'),
    path('subscription-requests/<int:pk>/approve/', views.approve_subscription_request, name='subscription_request_approve'),
    path('subscription-requests/<int:pk>/reject/', views.reject_subscription_request, name='subscription_request_reject'),

    path('live/', views.live_control_view, name='live_control'),

    path('support/', views.SupportMessageListView.as_view(), name='support_messages'),
    path('support/<int:pk>/reply/', views.support_message_reply, name='support_message_reply'),

    path('stats/', views.StatsView.as_view(), name='stats'),

    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
]
