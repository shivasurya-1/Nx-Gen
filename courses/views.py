from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
from django.db.models import Q

from accounts.permissions import IsStudent, IsInstructor
from .models import Course, CourseContent, Category, Module, Lesson, Submission, Batch
from .serializers import (
    CourseSerializer,
    CourseContentSerializer,
    CategorySerializer,
    ModuleSerializer,
    ModuleWriteSerializer,
    LessonSerializer,
    CourseContentDisplaySerializer,
    SubmissionSerializer,
    BatchSerializer,
)
from .permissions import IsSuperAdmin, IsAssignedInstructorOrAdmin, CanEditCourseContent, IsModuleCreator


# ════════════════════════════════════════════════════════════
# CATEGORY
# ════════════════════════════════════════════════════════════

class CategoryListCreateView(APIView):

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsSuperAdmin()]
        return [AllowAny()]

    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class CategoryDetailView(APIView):

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsSuperAdmin()]
        return [AllowAny()]

    def get(self, request, pk):
        try:
            category = Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)
        serializer = CategorySerializer(category)
        return Response(serializer.data)

    def put(self, request, pk):
        try:
            category = Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def patch(self, request, pk):
        return self.put(request, pk)

    def delete(self, request, pk):
        try:
            category = Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)
        category.delete()
        return Response({"message": "Category deleted"}, status=204)


# ════════════════════════════════════════════════════════════
# COURSE
# ════════════════════════════════════════════════════════════

class CourseListCreateView(APIView):

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsSuperAdmin()]
        return [AllowAny()]

    def get(self, request, category_id=None):
        courses = Course.objects.filter(is_active=True)
        if category_id is not None:
            courses = courses.filter(category_id=category_id)

        if request.user.is_authenticated:
            if request.user.role == 'student':
                from enrollments.models import Enrollment
                enrolled_ids = Enrollment.objects.filter(
                    email=request.user.email, status='approved'
                ).values_list('course_id', flat=True)
                courses = courses.filter(id__in=enrolled_ids)
            elif request.user.role == 'instructor':
                if hasattr(request.user, 'instructor'):
                    assigned_ids = request.user.instructor.assigned_courses.values_list('id', flat=True)
                    courses = courses.filter(id__in=assigned_ids)
                else:
                    courses = courses.none()

        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseDetailView(APIView):

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAssignedInstructorOrAdmin()]
        return [AllowAny()]

    def get(self, request, pk):
        try:
            course = Course.objects.get(pk=pk, is_active=True)
        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=404)

        if request.user.is_authenticated:
            if request.user.role == 'student':
                from enrollments.models import Enrollment
                if not Enrollment.objects.filter(
                    email=request.user.email, course=course, status='approved'
                ).exists():
                    return Response({"error": "You are not enrolled in this course"}, status=403)
            elif request.user.role == 'instructor':
                is_assigned = hasattr(request.user, 'instructor') and request.user.instructor.assigned_courses.filter(id=course.id).exists()
                if not is_assigned and not request.user.is_superuser:
                    return Response({"error": "You are not assigned to this course"}, status=403)

        serializer = CourseSerializer(course)
        return Response(serializer.data)

    def put(self, request, pk):
        try:
            course = Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=404)

        permission = IsAssignedInstructorOrAdmin()
        if not permission.has_object_permission(request, self, course):
            return Response({"error": "You don't have permission to edit this course"}, status=403)

        data = request.data.copy()
        # instructors cannot edit price
        if request.user.role == 'instructor' and not request.user.is_superuser:
            if 'price' in data:
                data.pop('price')

        serializer = CourseSerializer(course, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def patch(self, request, pk):
        return self.put(request, pk)

    def delete(self, request, pk):
        try:
            course = Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=404)

        permission = IsAssignedInstructorOrAdmin()
        if not permission.has_object_permission(request, self, course):
            return Response({"error": "You don't have permission to delete this course"}, status=403)

        course.delete()
        return Response({"message": "Course deleted"}, status=204)


# ════════════════════════════════════════════════════════════
# COURSE CONTENT  (full structured view — Training + Industry Readiness Modules)
# GET /courses/<id>/content/
# ════════════════════════════════════════════════════════════

class CourseContentView(APIView):
    """
    Returns the full structured content of a course
    """
    permission_classes = [AllowAny]

    def get(self, request, course_id):
        try:
            course = Course.objects.get(pk=course_id, is_active=True)
        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=404)

        # Role-based access check
        if request.user.is_authenticated:
            if request.user.role == 'student':
                from enrollments.models import Enrollment
                if not Enrollment.objects.filter(
                    email=request.user.email, course=course, status='approved'
                ).exists():
                    return Response({"error": "You are not enrolled in this course"}, status=403)
            elif request.user.role == 'instructor':
                is_assigned = hasattr(request.user, 'instructor') and request.user.instructor.assigned_courses.filter(id=course.id).exists()
                if not is_assigned and not request.user.is_superuser:
                    return Response({"error": "You are not assigned to this course"}, status=403)

        serializer = CourseContentDisplaySerializer(course, context={"request": request})
        return Response(serializer.data)


# ════════════════════════════════════════════════════════════
# OLD COURSE CONTENT MODEL (legacy)
# ════════════════════════════════════════════════════════════

class CourseContentListCreateView(APIView):

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAssignedInstructorOrAdmin()]
        return [AllowAny()]

    def get(self, request):
        if request.user.is_authenticated:
            if request.user.role == 'student':
                from enrollments.models import Enrollment
                enrolled_ids = Enrollment.objects.filter(
                    email=request.user.email, status='approved'
                ).values_list('course_id', flat=True)
                contents = CourseContent.objects.filter(course_id__in=enrolled_ids)
            elif request.user.role == 'instructor':
                if hasattr(request.user, 'instructor'):
                    assigned_ids = request.user.instructor.assigned_courses.values_list('id', flat=True)
                    contents = CourseContent.objects.filter(course_id__in=assigned_ids)
                else:
                    contents = CourseContent.objects.none()
            else:
                contents = CourseContent.objects.all()
        else:
            contents = CourseContent.objects.none()

        serializer = CourseContentSerializer(contents, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CourseContentSerializer(data=request.data)
        if serializer.is_valid():
            course = serializer.validated_data['course']
            permission = IsAssignedInstructorOrAdmin()
            if not permission.has_object_permission(request, self, course):
                return Response({"error": "You don't have permission to add content to this course"}, status=403)
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class CourseContentDetailView(APIView):

    def get_permissions(self):
        if self.request.method in ["PUT", "DELETE"]:
            return [CanEditCourseContent()]
        return [AllowAny()]

    def get(self, request, pk):
        try:
            content = CourseContent.objects.get(pk=pk)
        except CourseContent.DoesNotExist:
            return Response({"error": "Content not found"}, status=404)

        if request.user.is_authenticated:
            if request.user.role == 'student':
                from enrollments.models import Enrollment
                if not Enrollment.objects.filter(
                    email=request.user.email, course=content.course, status='approved'
                ).exists():
                    return Response({"error": "You are not enrolled in this course"}, status=403)
            elif request.user.role == 'instructor':
                is_assigned = hasattr(request.user, 'instructor') and request.user.instructor.assigned_courses.filter(id=content.course.id).exists()
                if not is_assigned and not request.user.is_superuser:
                    return Response({"error": "You are not assigned to this course"}, status=403)

        serializer = CourseContentSerializer(content)
        return Response(serializer.data)

    def put(self, request, pk):
        try:
            content = CourseContent.objects.get(pk=pk)
        except CourseContent.DoesNotExist:
            return Response({"error": "Content not found"}, status=404)

        permission = CanEditCourseContent()
        if not permission.has_object_permission(request, self, content):
            return Response({"error": "You don't have permission to edit this content"}, status=403)

        serializer = CourseContentSerializer(content, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def patch(self, request, pk):
        return self.put(request, pk)

    def delete(self, request, pk):
        try:
            content = CourseContent.objects.get(pk=pk)
        except CourseContent.DoesNotExist:
            return Response({"error": "Content not found"}, status=404)

        permission = CanEditCourseContent()
        if not permission.has_object_permission(request, self, content):
            return Response({"error": "You don't have permission to delete this content"}, status=403)

        content.delete()
        return Response({"message": "Content deleted"}, status=204)


# ════════════════════════════════════════════════════════════
# MODULE
# GET  /courses/<course_id>/modules/   → list modules
# POST /courses/<course_id>/modules/   → create module
# ════════════════════════════════════════════════════════════

class ModuleListCreateView(APIView):

    def get_permissions(self):
        if self.request.method == "POST":
            return [CanEditCourseContent()]
        return [AllowAny()]

    def get(self, request, course_id):
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=404)

        section_type = request.query_params.get("section_type")
        modules = Module.objects.filter(course=course).order_by('order')

        # Instructors should only see modules they created.
        # Admins keep full visibility.
        if request.user.is_authenticated and not request.user.is_superuser:
            if hasattr(request.user, 'instructor'):
                modules = modules.filter(created_by=request.user.instructor)
            else:
                modules = modules.none()

        if section_type:
            modules = modules.filter(section_type=section_type)
        
        serializer = ModuleSerializer(modules, many=True)
        return Response(serializer.data)

    def post(self, request, course_id):
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=404)

        # We pass course inside data as object permission checks against obj
        data = request.data.copy()
        data["course"] = course_id

        # To use CanEditCourseContent for course creation, we need mock obj or manual check
        permission = IsAssignedInstructorOrAdmin()
        if not permission.has_object_permission(request, self, course):
            return Response({"error": "You don't have permission to create modules for this course"}, status=403)

        serializer = ModuleWriteSerializer(data=data)
        if serializer.is_valid():
            if request.user.is_authenticated and hasattr(request.user, 'instructor'):
                module = serializer.save(created_by=request.user.instructor)
            else:
                module = serializer.save()
            return Response(ModuleSerializer(module).data, status=201)
        return Response(serializer.errors, status=400)


class ModuleDetailView(APIView):
    """
    GET    /courses/<course_id>/modules/<pk>/  → retrieve single module
    PUT    /courses/<course_id>/modules/<pk>/  → update module (instructor/admin)
    DELETE /courses/<course_id>/modules/<pk>/  → delete module (instructor/admin)
    """
    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsModuleCreator()]
        return [AllowAny()]

    def get(self, request, course_id, pk):
        try:
            module = Module.objects.get(pk=pk, course_id=course_id)
        except Module.DoesNotExist:
            return Response({"error": "Module not found in this course"}, status=404)
        serializer = ModuleSerializer(module)
        return Response(serializer.data)

    def put(self, request, course_id, pk):
        try:
            module = Module.objects.get(pk=pk, course_id=course_id)
        except Module.DoesNotExist:
            return Response({"error": "Module not found in this course"}, status=404)

        permission = IsModuleCreator()
        if not permission.has_object_permission(request, self, module):
            return Response({"error": "You can only edit modules you created"}, status=403)

        serializer = ModuleWriteSerializer(module, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def patch(self, request, course_id, pk):
        return self.put(request, course_id, pk)

    def delete(self, request, course_id, pk):
        try:
            module = Module.objects.get(pk=pk, course_id=course_id)
        except Module.DoesNotExist:
            return Response({"error": "Module not found in this course"}, status=404)

        permission = IsModuleCreator()
        if not permission.has_object_permission(request, self, module):
            return Response({"error": "You can only delete modules you created"}, status=403)

        module.delete()
        return Response({"message": "Module deleted"}, status=204)


# ════════════════════════════════════════════════════════════
# LESSON
# GET  /modules/<module_id>/lessons/   → list lessons
# POST /modules/<module_id>/lessons/   → create lesson
# ════════════════════════════════════════════════════════════

class LessonListCreateView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == "POST":
            return [CanEditCourseContent()]
        return [AllowAny()]

    def get(self, request, module_id):
        try:
            module = Module.objects.get(id=module_id)
        except Module.DoesNotExist:
            return Response({"error": "Module not found"}, status=404)

        lessons = Lesson.objects.filter(module=module).order_by('order')
        serializer = LessonSerializer(lessons, many=True)
        return Response(serializer.data)

    def post(self, request, module_id):
        try:
            module = Module.objects.get(id=module_id)
        except Module.DoesNotExist:
            return Response({"error": "Module not found"}, status=404)

        permission = CanEditCourseContent()
        if not permission.has_object_permission(request, self, module):
            return Response({"error": "You don't have permission to create lessons for this module"}, status=403)

        data = request.data.copy()
        data["module"] = module_id

        serializer = LessonSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class LessonDetailView(APIView):
    """
    GET    /modules/<module_id>/lessons/<pk>/  → retrieve single lesson
    PUT    /modules/<module_id>/lessons/<pk>/  → update lesson (instructor/admin)
    DELETE /modules/<module_id>/lessons/<pk>/  → delete lesson (instructor/admin)
    """
    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [CanEditCourseContent()]
        return [AllowAny()]

    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, module_id, pk):
        try:
            lesson = Lesson.objects.get(pk=pk, module_id=module_id)
        except Lesson.DoesNotExist:
            return Response({"error": "Lesson not found in this module"}, status=404)
        serializer = LessonSerializer(lesson)
        return Response(serializer.data)

    def put(self, request, module_id, pk):
        try:
            lesson = Lesson.objects.get(pk=pk, module_id=module_id)
        except Lesson.DoesNotExist:
            return Response({"error": "Lesson not found in this module"}, status=404)

        permission = CanEditCourseContent()
        if not permission.has_object_permission(request, self, lesson):
            return Response({"error": "You don't have permission to edit this lesson"}, status=403)

        serializer = LessonSerializer(lesson, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def patch(self, request, module_id, pk):
        return self.put(request, module_id, pk)

    def delete(self, request, module_id, pk):
        try:
            lesson = Lesson.objects.get(pk=pk, module_id=module_id)
        except Lesson.DoesNotExist:
            return Response({"error": "Lesson not found in this module"}, status=404)

        permission = CanEditCourseContent()
        if not permission.has_object_permission(request, self, lesson):
            return Response({"error": "You don't have permission to delete this lesson"}, status=403)

        lesson.delete()
        return Response({"message": "Lesson deleted"}, status=204)


class CourseCurriculumView(APIView):
    """Legacy endpoint — kept for backward compatibility."""
    permission_classes = [AllowAny]

    def get(self, request, course_id):
        path = request.build_absolute_uri(f"/api/courses/{course_id}/content/")
        return Response({"message": f"Use {path} instead for flat structure"}, status=410)


# ════════════════════════════════════════════════════════════
# SECTION TYPES
# ════════════════════════════════════════════════════════════

class SectionTypeListView(APIView):
    """
    GET /section-types/
    Returns the available section types for frontend dropdowns.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        from .models import Module
        
        # Build list from Django choices defined on the Module model
        data = [
            {"id": choice[0], "label": choice[1]}
            for choice in Module.SECTION_TYPES
        ]
        return Response(data)


# ════════════════════════════════════════════════════════════
# ASSIGNMENTS
# ════════════════════════════════════════════════════════════

class AssignmentCreateUpdateView(APIView):
    """
    POST /lessons/<lesson_id>/assignment/
    Allows an instructor or admin to create/update an assignment directly on a lesson.
    """
    def get_permissions(self):
        if self.request.method in ["POST", "PUT", "PATCH"]:
            return [CanEditCourseContent()]
        return [AllowAny()]
    
    def get(self, request, module_id, lesson_id):
        try:
            lesson = Lesson.objects.get(id=lesson_id, module_id=module_id)
        except Lesson.DoesNotExist:
            return Response({"error": "Lesson not found in this module"}, status=404)

        if not lesson.assignment_title:
            return Response({"error": "No assignment configured for this lesson"}, status=404)

        serializer = LessonSerializer(lesson)
        return Response(serializer.data)

    def put(self, request, module_id, lesson_id):
        return self.post(request, module_id, lesson_id)
        
    def patch(self, request, module_id, lesson_id):
        return self.post(request, module_id, lesson_id)

    def delete(self, request, module_id, lesson_id):
        try:
            lesson = Lesson.objects.get(id=lesson_id, module_id=module_id)
        except Lesson.DoesNotExist:
            return Response({"error": "Lesson not found in this module"}, status=404)

        permission = CanEditCourseContent()
        if not permission.has_object_permission(request, self, lesson):
            return Response({"error": "You don't have permission to delete assignments for this lesson"}, status=403)

        # Clear assignment fields
        lesson.assignment_title = ""
        lesson.assignment_description = ""
        lesson.assignment_due_date = None
        lesson.file = None
        lesson.save()

        # 🔥 Clear all student submissions for this lesson
        Submission.objects.filter(lesson=lesson).delete()

        return Response({"message": "Assignment record deleted successfully"}, status=204)

    def post(self, request, module_id, lesson_id):
        try:
            lesson = Lesson.objects.get(id=lesson_id, module_id=module_id)
        except Lesson.DoesNotExist:
            return Response({"error": "Lesson not found in this module"}, status=404)

        permission = CanEditCourseContent()
        if not permission.has_object_permission(request, self, lesson):
            return Response({"error": "You don't have permission to create assignments for this lesson"}, status=403)
        
        # Merge input data
        data = request.data.copy()

        was_assignment = bool(lesson.assignment_title)
        serializer = LessonSerializer(lesson, data=data, partial=True, context={'is_assignment': True})
        if serializer.is_valid():
            serializer.save()
            # If this is a fresh assignment creation on a previously non-assignment lesson,
            # clear any legacy submissions that might exist from previous assignment iterations.
            if not was_assignment:
                Submission.objects.filter(lesson=lesson).delete()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)


class AssignmentSubmitView(APIView):
    """
    POST /lessons/<lesson_id>/assignment/<assignment_id>/submit/
    (assignment_id is kept for URL compatibility — redirects to lesson_id)
    Student submits their assignment answer.
    """
    permission_classes = [AllowAny] # Checked manually for enrollment below
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, module_id, lesson_id, assignment_id=None):
        from .models import Lesson, Submission
        from enrollments.models import Enrollment

        if not request.user.is_authenticated or request.user.role != 'student':
            return Response({"error": "Only enrolled students can submit assignments."}, status=403)

        try:
            lesson = Lesson.objects.filter(id=lesson_id, module_id=module_id).exclude(assignment_title="").first()
            if not lesson: raise Lesson.DoesNotExist
        except Lesson.DoesNotExist:
            return Response({"error": "Lesson assignment not found in this module"}, status=404)

        # Check enrollment via course
        course = lesson.module.course
        if not Enrollment.objects.filter(email=request.user.email, course=course, status='approved').exists():
            return Response({"error": "You are not enrolled in this course."}, status=403)

        # If this lesson is instructor-specific, only students from that instructor's active batches can submit.
        lesson_instructor = lesson.module.created_by
        if lesson_instructor:
            is_student_in_batch = Batch.objects.filter(
                course=course,
                instructor=lesson_instructor,
                is_active=True,
                students=request.user,
            ).exists()
            if not is_student_in_batch:
                return Response({"error": "This assignment is not assigned to your batch."}, status=403)

        # Check if already submitted
        submission = Submission.objects.filter(lesson=lesson, student=request.user).first()
        
        # Only allow answer payload from students.
        data = {
            'lesson': lesson.id,
            'student': request.user.id,
            'status': 'submitted',
            'text_answer': request.data.get('text_answer', ''),
            'file_upload': request.data.get('file_upload'),
            # Re-submission invalidates prior grading.
            'score': None,
            'feedback': '',
            'graded_at': None,
            'graded_by': None,
        }

        if submission:
            # Update existing submission
            serializer = SubmissionSerializer(submission, data=data, partial=True)
        else:
            # Create new submission
            serializer = SubmissionSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class AssignmentStatusView(APIView):
    """
    GET /lessons/<lesson_id>/assignment/<assignment_id>/status/
    Returns a unified list of enrolled students along with their submission status for a specific lesson's assignment.
    """
    def get_permissions(self):
        return [IsAssignedInstructorOrAdmin()]

    def get(self, request, module_id, lesson_id, assignment_id=None):
        from .models import Lesson, Submission
        from enrollments.models import Enrollment
        from django.contrib.auth import get_user_model

        User = get_user_model()

        try:
            lesson = Lesson.objects.filter(id=lesson_id, module_id=module_id).exclude(assignment_title="").first()
            if not lesson: raise Lesson.DoesNotExist
        except Lesson.DoesNotExist:
            return Response({"error": "Lesson assignment not found in this module"}, status=404)

        course = lesson.module.course
        
        # Verify permissions 
        permission = IsAssignedInstructorOrAdmin()
        if not permission.has_object_permission(request, self, course):
            return Response({"error": "You don't have permission to view status for this assignment"}, status=403)

        # Build student scope.
        # - Admin: all approved enrollments in this course.
        # - Instructor: only students in instructor's active batches for this course.
        if request.user.is_superuser:
            approved_emails = Enrollment.objects.filter(course=course, status='approved').values_list('email', flat=True)
            enrolled_users = User.objects.filter(email__in=approved_emails).prefetch_related('enrolled_batches')
        elif hasattr(request.user, 'instructor'):
            instructor_batches = Batch.objects.filter(
                course=course,
                instructor=request.user.instructor,
                is_active=True,
            )
            enrolled_users = User.objects.filter(
                id__in=instructor_batches.values_list('students__id', flat=True)
            ).distinct().prefetch_related('enrolled_batches')
        else:
            enrolled_users = User.objects.none()

        # Get all submissions for this lesson
        submissions = Submission.objects.filter(lesson=lesson)
        submission_map = {sub.student_id: sub for sub in submissions}

        # Build response
        response_data = []
        for user in enrolled_users:
            sub = submission_map.get(user.id)
            
            # Find batch for this student in this course
            if request.user.is_superuser:
                batch = user.enrolled_batches.filter(course=course, is_active=True).first()
            elif hasattr(request.user, 'instructor'):
                batch = user.enrolled_batches.filter(
                    course=course,
                    is_active=True,
                    instructor=request.user.instructor,
                ).first()
            else:
                batch = None
            batch_data = {"id": batch.id, "name": batch.name} if batch else None

            if sub:
                response_data.append({
                    "submission_id": sub.id,
                    "student_id": user.id,
                    "student_name": f"{user.first_name} {user.last_name}".strip() or user.email,
                    "student_email": user.email,
                    "batch": batch_data,
                    "status": "Submitted",
                    "submitted_at": sub.submitted_at,
                    "score": sub.score,
                    "feedback": sub.feedback,
                    "graded_at": sub.graded_at,
                    "graded_by": f"{sub.graded_by.first_name} {sub.graded_by.last_name}".strip() or sub.graded_by.email if sub.graded_by else None,
                    "submission_data": SubmissionSerializer(sub).data
                })
            else:
                response_data.append({
                    "submission_id": None,
                    "student_id": user.id,
                    "student_name": f"{user.first_name} {user.last_name}".strip() or user.email,
                    "student_email": user.email,
                    "batch": batch_data,
                    "status": "Not Submitted",
                    "submitted_at": None,
                    "score": None,
                    "feedback": "",
                    "graded_at": None,
                    "graded_by": None,
                    "submission_data": None
                })

        return Response(response_data, status=200)


class AssignmentGradeView(APIView):
    """
    PATCH /modules/<module_id>/lessons/<lesson_id>/assignment/submissions/<submission_id>/grade/
    Allows assigned instructor/admin to grade an existing submission.
    """

    def get_permissions(self):
        return [IsAssignedInstructorOrAdmin()]

    def patch(self, request, module_id, lesson_id, submission_id):
        try:
            lesson = Lesson.objects.get(id=lesson_id, module_id=module_id)
        except Lesson.DoesNotExist:
            return Response({"error": "Lesson not found in this module"}, status=404)

        if not lesson.assignment_title:
            return Response({"error": "No assignment configured for this lesson"}, status=404)

        course = lesson.module.course
        permission = IsAssignedInstructorOrAdmin()
        if not permission.has_object_permission(request, self, course):
            return Response({"error": "You don't have permission to grade this assignment"}, status=403)

        try:
            submission = Submission.objects.get(id=submission_id, lesson=lesson)
        except Submission.DoesNotExist:
            return Response({"error": "Submission not found for this assignment"}, status=404)

        score_raw = request.data.get("score")
        feedback = (request.data.get("feedback") or "").strip()

        if score_raw in (None, ""):
            return Response({"error": "score is required"}, status=400)

        try:
            score = int(score_raw)
        except (TypeError, ValueError):
            return Response({"error": "score must be an integer"}, status=400)

        if score < 0 or score > 100:
            return Response({"error": "score must be between 0 and 100"}, status=400)

        submission.score = score
        submission.feedback = feedback
        submission.status = "graded"
        submission.graded_at = timezone.now()
        submission.graded_by = request.user
        submission.save(update_fields=["score", "feedback", "status", "graded_at", "graded_by"])

        return Response(SubmissionSerializer(submission).data, status=200)

class InstructorStudentDetailView(APIView):
    """
    GET /student-assignments/<student_id>/
    Returns list of assignments for a specific student across their enrolled courses, 
    with submission status. Useful for instructor detail view.
    """
    def get_permissions(self):
        from accounts.permissions import IsInstructor
        return [IsInstructor()]

    def get(self, request, student_id):
        from django.contrib.auth import get_user_model
        from enrollments.models import Enrollment
        from .models import Lesson, Submission
        
        User = get_user_model()
        try:
            student = User.objects.get(id=student_id)
        except User.DoesNotExist:
            return Response({"error": "Student not found"}, status=404)

        # Get courses this student is enrolled in that are also assigned to this instructor (or all if admin)
        enrollment_qs = Enrollment.objects.filter(email=student.email, status='approved')
        
        if not request.user.is_superuser and hasattr(request.user, 'instructor'):
            assigned_courses = request.user.instructor.assigned_courses.all()
            enrollment_qs = enrollment_qs.filter(course__in=assigned_courses)
        elif not request.user.is_superuser:
             return Response({"error": "Instructor profile not found."}, status=403)

        enrolled_course_ids = enrollment_qs.values_list('course_id', flat=True)

        lessons = Lesson.objects.filter(
            module__course__id__in=enrolled_course_ids
        ).exclude(assignment_title="").select_related('module__course')

        data = []
        for lesson in lessons:
            submission = Submission.objects.filter(
                lesson=lesson, student=student
            ).first()
            data.append({
                "assignment": LessonSerializer(lesson).data,
                "course": {
                    "id": lesson.module.course.id,
                    "title": lesson.module.course.title,
                },
                "status": submission.status if submission else "Not Submitted",
                "submitted_at": submission.submitted_at if submission else None,
                "submission_data": SubmissionSerializer(submission).data if submission else None
            })

        return Response(data)


class AssignmentDetailView(APIView):
    """
    GET    /lessons/<lesson_id>/assignment/<pk>/  → retrieve assignment details
    PUT    /lessons/<lesson_id>/assignment/<pk>/  → update assignment (instructor/admin)
    DELETE /lessons/<lesson_id>/assignment/<pk>/  → delete assignment (instructor/admin)
    """
    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [CanEditCourseContent()]
        return [AllowAny()]

    def get(self, request, lesson_id, pk=None):
        try:
            lesson = Lesson.objects.filter(id=lesson_id).exclude(assignment_title="").first()
            if not lesson: raise Lesson.DoesNotExist
        except Lesson.DoesNotExist:
            return Response({"error": "Assignment not found for this lesson"}, status=404)
        serializer = LessonSerializer(lesson)
        return Response(serializer.data)

    def put(self, request, lesson_id, pk=None):
        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return Response({"error": "Lesson not found"}, status=404)

        permission = CanEditCourseContent()
        if not permission.has_object_permission(request, self, lesson):
            return Response({"error": "You don't have permission to edit this assignment"}, status=403)

        data = request.data.copy()

        was_assignment = bool(lesson.assignment_title)
        serializer = LessonSerializer(lesson, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # If this becomes a fresh assignment or title is set for the first time, clear legacy data.
            if not was_assignment and lesson.assignment_title:
                Submission.objects.filter(lesson=lesson).delete()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def patch(self, request, lesson_id, pk=None):
        return self.put(request, lesson_id, pk)

    def delete(self, request, lesson_id, pk=None):
        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return Response({"error": "Lesson not found"}, status=404)

        permission = CanEditCourseContent()
        if not permission.has_object_permission(request, self, lesson):
            return Response({"error": "You don't have permission to delete this assignment"}, status=403)

        # Deleting assignment means clearing title on the lesson
        lesson.assignment_title = ""
        lesson.assignment_description = ""
        lesson.save()

        # 🔥 CRITICAL: Remove all student submissions for this lesson when the assignment is deleted.
        Submission.objects.filter(lesson=lesson).delete()

        return Response({"message": "Assignment removed from lesson"}, status=204)


class StudentAssignmentListView(APIView):
    """
    GET /my-assignments/
    Returns all lessons marked as assignments for a student's enrolled courses,
    along with their submission status.
    """
    def get_permissions(self):
        return [IsStudent()]

    def get(self, request):
        from enrollments.models import Enrollment

        enrolled_course_ids = Enrollment.objects.filter(
            email=request.user.email,
            status='approved'
        ).values_list('course_id', flat=True)

        student_batches = Batch.objects.filter(
            students=request.user,
            is_active=True,
            course_id__in=enrolled_course_ids,
        )
        batch_instructor_ids = list(
            student_batches.exclude(instructor__isnull=True).values_list('instructor_id', flat=True)
        )

        lessons_qs = Lesson.objects.filter(
            module__course__id__in=enrolled_course_ids
        ).exclude(assignment_title="")

        # Show all assignments in the student's enrolled courses.
        lessons = lessons_qs.select_related('module__course')

        data = []
        for lesson in lessons:
            submission = Submission.objects.filter(
                lesson=lesson, student=request.user
            ).first()
            data.append({
                "assignment": LessonSerializer(lesson).data,
                "course": {
                    "id": lesson.module.course.id,
                    "title": lesson.module.course.title,
                },
                "status": submission.status if submission else "Not Submitted",
                "submitted_at": submission.submitted_at if submission else None,
            })

        return Response(data)


class InstructorAssignmentListView(APIView):
    """
    GET /instructor-assignments/
    Returns all lessons marked as assignments across courses the instructor is assigned to.
    """
    def get_permissions(self):
        return [IsAssignedInstructorOrAdmin()]

    def get(self, request):
        if request.user.is_superuser:
            lessons = Lesson.objects.exclude(assignment_title="")
        else:
            if hasattr(request.user, 'instructor'):
                assigned_courses = request.user.instructor.assigned_courses.all()
                lessons = Lesson.objects.filter(
                    module__course__in=assigned_courses,
                ).exclude(assignment_title="")
            else:
                lessons = Lesson.objects.none()

        lessons = lessons.select_related('module__course')

        data = []
        for lesson in lessons:
            submission_count = Submission.objects.filter(lesson=lesson).count()
            data.append({
                "assignment": LessonSerializer(lesson).data,
                "course": {
                    "id": lesson.module.course.id,
                    "title": lesson.module.course.title,
                },
                "module": {
                    "id": lesson.module.id,
                    "title": lesson.module.title,
                },
                "lesson": {
                    "id": lesson.id,
                    "title": lesson.title,
                },
                "submissions_count": submission_count,
            })

        return Response(data)


# ════════════════════════════════════════════════════════════
# BATCHES
# ════════════════════════════════════════════════════════════

class BatchListCreateView(APIView):
    def get_permissions(self):
        # IsSuperAdmin is already imported from courses.permissions at top of this file
        if self.request.method == "POST":
            return [IsSuperAdmin()]
        # GET is open to authenticated users; filtering happens in get()
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]

    def get(self, request):
        batches = Batch.objects.filter(is_active=True).order_by('-created_at')
        if request.user.is_authenticated:
            if getattr(request.user, 'role', '') == 'instructor' and not request.user.is_superuser:
                if hasattr(request.user, 'instructor'):
                    batches = batches.filter(instructor=request.user.instructor)
                else:
                    batches = batches.none()
        else:
            batches = batches.none() # Return nothing for unauthenticated

        serializer = BatchSerializer(batches, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BatchSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BatchDetailView(APIView):
    def get_permissions(self):
        return [IsSuperAdmin()]

    def get(self, request, pk):
        try:
            batch = Batch.objects.get(pk=pk)
            serializer = BatchSerializer(batch)
            return Response(serializer.data)
        except Batch.DoesNotExist:
            return Response({"error": "Batch not found"}, status=404)

    def put(self, request, pk):
        try:
            batch = Batch.objects.get(pk=pk)
        except Batch.DoesNotExist:
            return Response({"error": "Batch not found"}, status=404)

        serializer = BatchSerializer(batch, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def patch(self, request, pk):
        return self.put(request, pk)

    def delete(self, request, pk):
        try:
            batch = Batch.objects.get(pk=pk)
            batch.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Batch.DoesNotExist:
            return Response({"error": "Batch not found"}, status=404)

class ManageBatchStudentsView(APIView):
    def get_permissions(self):
        return [IsSuperAdmin()]

    def post(self, request, pk):
        try:
            batch = Batch.objects.get(pk=pk)
        except Batch.DoesNotExist:
            return Response({"error": "Batch not found"}, status=404)
        
        student_emails = request.data.get('student_emails', [])
        action = request.data.get('action', 'add')

        from django.contrib.auth import get_user_model
        User = get_user_model()
        students = User.objects.filter(email__in=student_emails)

        if action == 'add':
            batch.students.add(*students)
        elif action == 'remove':
            batch.students.remove(*students)
            
        return Response({"message": "Batch students updated successfully."})

class InstructorBatchListView(APIView):
    def get_permissions(self):
        from accounts.permissions import IsInstructor
        return [IsInstructor()]

    def get(self, request):
        if hasattr(request.user, 'instructor'):
            batches = request.user.instructor.batches.filter(is_active=True).prefetch_related('students', 'course')
            
            data = []
            for batch in batches:
                data.append({
                    "id": batch.id,
                    "name": batch.name,
                    "course_id": batch.course.id,
                    "course_title": batch.course.title,
                    "live_link": batch.live_link,
                    "is_live_class_active": batch.is_live_class_active,
                    "students": [
                        {
                            "id": student.id,
                            "name": f"{student.first_name} {student.last_name}".strip() or student.email,
                            "email": student.email,
                            "phone": getattr(student, 'phone', None)
                        } for student in batch.students.all()
                    ]
                })
            return Response(data)
        return Response({"error": "Instructor profile not found."}, status=403)


class ManageLiveClassView(APIView):
    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]

    def post(self, request, pk):
        try:
            batch = Batch.objects.get(pk=pk)
        except Batch.DoesNotExist:
            return Response({'error': 'Batch not found'}, status=404)

        if request.user.role == 'instructor':
            if not hasattr(request.user, 'instructor') or batch.instructor != request.user.instructor:
                return Response({'error': 'Not assigned to this batch'}, status=403)
        elif request.user.role != 'admin' and not request.user.is_superuser:
            return Response({'error': 'Permission denied'}, status=403)

        action = request.data.get('action')
        if action == 'start':
            link = request.data.get('live_link')
            if not link:
                return Response({'error': 'Meeting link is required'}, status=400)
            batch.live_link = link
            batch.is_live_class_active = True
            batch.save()
            return Response({'message': 'Live class started', 'live_link': batch.live_link})
        elif action == 'end':
            batch.is_live_class_active = False
            batch.live_link = ''
            batch.save()
            return Response({'message': 'Live class ended'})

        return Response({'error': 'Invalid action'}, status=400)

