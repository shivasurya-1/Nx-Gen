from rest_framework import serializers
from .models import Category, Course, CourseContent, Module, Lesson, Submission, Batch


# ─────────────────────────────────────────────
# LESSON
# ─────────────────────────────────────────────
class LessonSerializer(serializers.ModelSerializer):
    assignment_due_date = serializers.DateTimeField(required=False, allow_null=True)

    def to_internal_value(self, data):
        # Handle empty strings from frontend for assignment_due_date (previously called due_date)
        if 'assignment_due_date' in data and data['assignment_due_date'] in ["", "null", "undefined", None]:
            data = data.copy()
            data['assignment_due_date'] = None
        # Support legacy frontend keys if still using "due_date"
        elif 'due_date' in data and data['due_date'] in ["", "null", "undefined", None]:
            data = data.copy()
            data['assignment_due_date'] = None
            
        return super().to_internal_value(data)

    class Meta:
        model = Lesson
        fields = "__all__"


# ─────────────────────────────────────────────
# MODULE  (nested lessons — read only)
# ─────────────────────────────────────────────
class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = "__all__"
        read_only_fields = ("created_by", "created_at", "updated_at")


# ─────────────────────────────────────────────
# MODULE  (write — no nested lessons)
# ─────────────────────────────────────────────
class ModuleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = "__all__"
        read_only_fields = ("created_by", "created_at", "updated_at")


# ─────────────────────────────────────────────
# COURSE CONTENT  (full structured display)
# Returns course with separated modules for
# training and industry_readiness
# ─────────────────────────────────────────────
class CourseContentDisplaySerializer(serializers.ModelSerializer):
    """
    Full read-only representation of a course's content:
      {
         "id": 1,
         ...
         "training_modules": [...],
         "industry_readiness_modules": [...]
      }
    """
    training_modules = serializers.SerializerMethodField()
    industry_readiness_modules = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id", "title", "description", "price",
            "category",
            "training_modules", "industry_readiness_modules",
        ]

    def get_training_modules(self, course):
        modules = course.modules.filter(section_type="training").order_by("order")
        return ModuleSerializer(modules, many=True).data

    def get_industry_readiness_modules(self, course):
        modules = course.modules.filter(section_type="industry_readiness").order_by("order")
        return ModuleSerializer(modules, many=True).data


# ─────────────────────────────────────────────
# COURSE CONTENT MODEL (legacy — kept)
# ─────────────────────────────────────────────
class CourseContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseContent
        fields = "__all__"


# ─────────────────────────────────────────────
# COURSE
# ─────────────────────────────────────────────
class CourseSerializer(serializers.ModelSerializer):
    contents = CourseContentSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = "__all__"


# ─────────────────────────────────────────────
# CATEGORY
# ─────────────────────────────────────────────
class CategorySerializer(serializers.ModelSerializer):
    courses = CourseSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = "__all__"


# ─────────────────────────────────────────────
# SUBMISSION
# ─────────────────────────────────────────────
class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = "__all__"


# ─────────────────────────────────────────────
# BATCH
# ─────────────────────────────────────────────
class BatchSerializer(serializers.ModelSerializer):
    students_detail = serializers.SerializerMethodField()
    course_title = serializers.ReadOnlyField(source='course.title')

    class Meta:
        model = Batch
        fields = "__all__"

    def get_students_detail(self, obj):
        return [
            {
                "id": s.id,
                "name": f"{s.first_name} {s.last_name}".strip() or s.email,
                "email": s.email,
            }
            for s in obj.students.all()
        ]

    def validate(self, attrs):
        instance = getattr(self, "instance", None)
        if instance and instance.instructor_id:
            if "instructor" in attrs and attrs["instructor"] != instance.instructor:
                raise serializers.ValidationError({
                    "instructor": "Instructor cannot be changed after the batch is assigned."
                })
        return attrs