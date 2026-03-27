from django.urls import path
from .views import (
    EnrollView,
    EnrollmentListView,
    ApproveEnrollmentView,
    RejectEnrollmentView,
    CreateOrderView,
    VerifyPaymentView,
    StudentCoursesView,
    StudentDashboardStatsView
)

urlpatterns = [
    path('enroll/', EnrollView.as_view()),
    path('student/courses/', StudentCoursesView.as_view()),
    path('student/dashboard-stats/', StudentDashboardStatsView.as_view()),
    path('admin/enrollments/', EnrollmentListView.as_view()),
    path('admin/enrollments/<int:id>/approve/', ApproveEnrollmentView.as_view()),
    path('admin/enrollments/<int:id>/reject/', RejectEnrollmentView.as_view()),
    path('create-order/', CreateOrderView.as_view()),
    path('verify-payment/', VerifyPaymentView.as_view()), 
]
