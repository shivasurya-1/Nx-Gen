from rest_framework.permissions import BasePermission
from enrollments.models import Enrollment
from instructors.models import Instructor

class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class IsEnrolledStudent(BasePermission):
    """
    Allows students to view only courses they are enrolled in
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role != 'student':
            return False

        # Check if student is enrolled in this course
        return Enrollment.objects.filter(
            email=request.user.email,
            course=obj,
            status='approved'
        ).exists()


class IsAssignedInstructorOrAdmin(BasePermission):
    """
    Allows instructors to access courses assigned to them,
    and admins to access all courses
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Admins can access everything
        if request.user.is_superuser:
            return True

        # Instructors can access their assigned courses
        if hasattr(request.user, 'instructor'):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Admins can access everything
        if request.user.is_superuser:
            return True

        # Instructors can only access courses assigned to them
        if hasattr(request.user, 'instructor'):
            return request.user.instructor.assigned_courses.filter(id=obj.id).exists()

        return False


class CanEditCourseContent(BasePermission):
    """
    Allows instructors to edit content of courses assigned to them,
    and admins to edit all course content
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Admins can edit everything
        if request.user.is_superuser:
            return True

        # Instructors can only edit courses assigned to them
        if hasattr(request.user, 'instructor'):
            course_id = None
            if hasattr(obj, 'course'):
                course_id = obj.course.id
            # For Lesson, check through module
            elif hasattr(obj, 'module'):
                course_id = obj.module.course.id
            # For Assignment, check through lesson → module → course
            elif hasattr(obj, 'lesson'):
                course_id = obj.lesson.module.course.id
            else:
                return False
                
            return request.user.instructor.assigned_courses.filter(id=course_id).exists()

        return False


class IsModuleCreator(BasePermission):
    """
    Allows only the instructor who created the module to edit/delete it.
    Admins can manage any module.
    
    This ensures modules are instructor-specific and not shared across
    different instructors assigned to the same course.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Admins can edit/delete any module
        if request.user.is_superuser:
            return True

        # Instructors can only edit/delete modules they created
        if hasattr(request.user, 'instructor'):
            # Check if the current instructor is the creator of this module
            return obj.created_by == request.user.instructor

        return False
