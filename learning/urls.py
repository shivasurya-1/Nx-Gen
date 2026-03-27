from django.urls import path
from .views import SaveProgressView, CourseProgressView, LessonProgressView, LessonDetailView, RecentProgressView

urlpatterns = [
    path('progress/save/', SaveProgressView.as_view(), name='save_progress'),
    path('progress/course/<int:course_id>/', CourseProgressView.as_view(), name='course_progress'),
    path('progress/lesson/<int:lesson_id>/', LessonProgressView.as_view(), name='lesson_progress'),
    path('progress/recent/', RecentProgressView.as_view(), name='recent_progress'),
    path('lesson/<int:lesson_id>/Detail/', LessonDetailView.as_view(), name='lesson_detail'),
]