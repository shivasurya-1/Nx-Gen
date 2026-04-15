from django.urls import path
from .views import (
    # Category
    CategoryListCreateView,
    CategoryDetailView,
    # Course
    CourseListCreateView,
    CourseDetailView,
    # Course content (full structured)
    CourseContentView,
    # Legacy course content model
    CourseContentListCreateView,
    CourseContentDetailView,
    # Modules
    ModuleListCreateView,
    ModuleDetailView,
    # Lessons
    LessonListCreateView,
    LessonDetailView,
    # Legacy full curriculum
    CourseCurriculumView,
    # Assignments
    AssignmentCreateUpdateView,
    AssignmentSubmitView,
    AssignmentStatusView,
    AssignmentGradeView,
    # Student / Instructor assignment overview
    StudentAssignmentListView,
    InstructorAssignmentListView,
    InstructorStudentDetailView,
    # Section Types
    SectionTypeListView,
    # Batches
    BatchListCreateView,
    BatchDetailView,
    ManageBatchStudentsView,
    InstructorBatchListView,
    ManageLiveClassView,
)

urlpatterns = [

    # ── CATEGORY ──────────────────────────────────────────────────────────
    path('categories/', CategoryListCreateView.as_view()),
    path('categories/<int:pk>/', CategoryDetailView.as_view()),

    # ── COURSE ────────────────────────────────────────────────────────────
    path('courses/', CourseListCreateView.as_view()),
    path('categories/<int:category_id>/courses/', CourseListCreateView.as_view()),
    path('courses/<int:pk>/', CourseDetailView.as_view()),

    # ── COURSE CONTENT (full structured view) ─────────────────────────────
    path('courses/<int:course_id>/content/', CourseContentView.as_view()),

    # ── MODULES ───────────────────────────────────────────────────────────
    # GET  → list modules in that course (optional ?section_type=training)
    # POST → add a new module to that course (pass section_type in payload)
    path('courses/<int:course_id>/modules/', ModuleListCreateView.as_view()),
    # GET / PUT / DELETE → single module
    path('courses/<int:course_id>/modules/<int:pk>/', ModuleDetailView.as_view()),

    # ── LESSONS UNDER A MODULE ────────────────────────────────────────────
    # GET  → list lessons in that module
    # POST → add a new lesson to that module
    path('modules/<int:module_id>/lessons/', LessonListCreateView.as_view()),
    # GET / PUT / DELETE → single lesson
    path('modules/<int:module_id>/lessons/<int:pk>/', LessonDetailView.as_view()),

    # ── LEGACY ────────────────────────────────────────────────────────────
    path('content/', CourseContentListCreateView.as_view()),
    path('content/<int:pk>/', CourseContentDetailView.as_view()),
    path('courses/<int:course_id>/curriculum/', CourseCurriculumView.as_view()),

    # ── ASSIGNMENTS ───────────────────────────────────────────────────────
    # Create/update/get assignment on a lesson (instructor)
    path('modules/<int:module_id>/lessons/<int:lesson_id>/assignment/', AssignmentCreateUpdateView.as_view()),
    # Student submits answer
    path('modules/<int:module_id>/lessons/<int:lesson_id>/assignment/submit/', AssignmentSubmitView.as_view()),
    # Instructor views all student statuses for an assignment
    path('modules/<int:module_id>/lessons/<int:lesson_id>/assignment/status/', AssignmentStatusView.as_view()),
    # Instructor grades a specific student submission
    path('modules/<int:module_id>/lessons/<int:lesson_id>/assignment/submissions/<int:submission_id>/grade/', AssignmentGradeView.as_view()),

    # ── ASSIGNMENT OVERVIEWS ──────────────────────────────────────────────
    # Student: list all assignments across enrolled courses + submission status
    path('my-assignments/', StudentAssignmentListView.as_view()),
    # Instructor: list all assignments across their courses
    path('instructor-assignments/', InstructorAssignmentListView.as_view()),
    path('student-assignments/<int:student_id>/', InstructorStudentDetailView.as_view()),

    # ── METADATA ──────────────────────────────────────────────────────────
    path('section-types/', SectionTypeListView.as_view()),

    # ── BATCHES ───────────────────────────────────────────────────────────
    path('batches/', BatchListCreateView.as_view()),
    path('batches/<int:pk>/', BatchDetailView.as_view()),
    path('batches/<int:pk>/manage_students/', ManageBatchStudentsView.as_view()),
    path('batches/<int:pk>/live_class/', ManageLiveClassView.as_view()),
    # Instructor Batches
    path('my-batches/', InstructorBatchListView.as_view()),
]