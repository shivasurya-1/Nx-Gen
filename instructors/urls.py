from django.urls import path
from .views import (
    InstructorRegisterView,
    DeactivateInstructorView,
    ActivateInstructorView,
    InstructorListView,
    InstructorCoursesView,
    InstructorProfileView,
    InstructorDetailByIdView,
)

urlpatterns = [

    # 🔥 Register Instructor (Admin creates instructor)
    path('register/', InstructorRegisterView.as_view(), name='instructor-register'),

    # 🔥 Get / Update single instructor by ID (admin)
    path('<int:id>/', InstructorDetailByIdView.as_view(), name='instructor-detail'),

    # 🔥 Deactivate Instructor
    path('<int:id>/deactivate/', DeactivateInstructorView.as_view(), name='deactivate-instructor'),

    # 🔥 Activate Instructor
    path('<int:id>/activate/', ActivateInstructorView.as_view(), name='activate-instructor'),

    # 🔥 List all instructors (optional)
    path('', InstructorListView.as_view(), name='instructor-list'),

 
    path('my-courses/', InstructorCoursesView.as_view()),


    path('profile/', InstructorProfileView.as_view()),


]