from rest_framework import serializers
from .models import Enrollment


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = "__all__"
        read_only_fields = ["status", "is_active"]

    def validate(self, data):
        if not data.get("terms_accepted"):
            raise serializers.ValidationError("You must accept terms & conditions")

        if Enrollment.objects.filter(
            email=data.get("email"),
            course=data.get("course")
        ).exists():
            raise serializers.ValidationError("Already enrolled for this course")

        return data

from courses.models import Lesson
from learning.models import LessonProgress

class StudentEnrolledCourseSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    instructor_name = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    completed_lessons = serializers.SerializerMethodField()
    total_lessons = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = ['id', 'course_id', 'course_title', 'instructor_name', 'progress', 'completed_lessons', 'total_lessons', 'status']

    def get_instructor_name(self, obj):
        instructor = obj.course.instructor_assigned_courses.first()
        return instructor.full_name if instructor else 'Assigned soon'

    def get_total_lessons(self, obj):
        return Lesson.objects.filter(module__course=obj.course).count()

    def get_completed_lessons(self, obj):
        user = self.context.get('request').user
        return LessonProgress.objects.filter(student=user, lesson__module__course=obj.course, completed=True).count()

    def get_progress(self, obj):
        total = self.get_total_lessons(obj)
        if total == 0: return 0
        return round((self.get_completed_lessons(obj) / total) * 100)

