# serializers.py

from rest_framework import serializers
from .models import Instructor
from courses.models import Course
from django.contrib.auth import get_user_model
import random
import string

User = get_user_model()


class InstructorCreateSerializer(serializers.ModelSerializer):

    assigned_courses = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        many=True,
        required=True
    )

    class Meta:
        model = Instructor
        fields = [
            "full_name",
            "phone",
            "employee_id",
            "date_of_joining",
            "qualification",
            "experience",
            "bank_account_number",
            "ifsc_code",
            "pan_number",
            "aadhaar_number",
            "assigned_courses",
            "email"
        ]

    def create(self, validated_data):
        courses = validated_data.pop("assigned_courses", [])
        email = validated_data["email"]

        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        user = User.objects.filter(email=email).first()

        if not user:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                role="instructor"   # ✅ SET ROLE HERE
            )
        else:
            # 🔥 UPDATE ROLE IF EXISTS
            user.role = "instructor"
            user.set_password(password)
            user.save()

        user.is_active = True
        user.is_staff = True
        user.save()

        # 🔥 ✅ ADD THIS CHECK HERE
        if Instructor.objects.filter(user=user).exists():
            raise serializers.ValidationError("Instructor already exists")

        instructor = Instructor.objects.create(
            user=user,
            is_active=True,
            is_first_login=True,
            **validated_data
        )

        instructor.assigned_courses.set(courses)

        from .tasks import send_instructor_credentials_email_task

        send_instructor_credentials_email_task.delay(
            email,
            validated_data["full_name"],
            user.username,
            password
        )

        return instructor


# 🔹 List Serializer (clean output)
class InstructorListSerializer(serializers.ModelSerializer):
    courses = serializers.SerializerMethodField()

    class Meta:
        model = Instructor
        fields = [
            "id",
            "full_name",
            "email",
            "phone",
            "employee_id",
            "experience",
            "qualification",
            "date_of_joining",
            "is_active",
            "courses",
            "created_at"
        ]

    def get_courses(self, obj):
        return [
            {"id": c.id, "title": c.title}
            for c in obj.assigned_courses.all()
        ]
    
class InstructorDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Instructor
        fields = "__all__"

    def update(self, instance, validated_data):

        request = self.context.get("request")
        user = request.user

        # 🔥 If instructor → block bank fields
        if hasattr(user, "instructor") and not user.is_superuser:

            restricted_fields = [
                "bank_account_number",
                "ifsc_code",
                "pan_number",
                "aadhaar_number"
            ]

            for field in restricted_fields:
                if field in validated_data:
                    validated_data.pop(field)

        return super().update(instance, validated_data)