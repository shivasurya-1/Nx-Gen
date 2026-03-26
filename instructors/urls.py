from django.urls import path
from .views import (
    InstructorRegisterView,
    DeactivateInstructorView,
    InstructorListView,
    InstructorCoursesView,
    InstructorProfileView

)

urlpatterns = [

    # 🔥 Register Instructor (Admin creates instructor)
    path('register/', InstructorRegisterView.as_view(), name='instructor-register'),

    # 🔥 Deactivate Instructor
    path('<int:id>/deactivate/', DeactivateInstructorView.as_view(), name='deactivate-instructor'),

    # 🔥 List all instructors (optional)
    path('', InstructorListView.as_view(), name='instructor-list'),

 
    path('my-courses/', InstructorCoursesView.as_view()),


    path('profile/', InstructorProfileView.as_view()),


]