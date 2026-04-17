# serializers.py

from rest_framework import serializers
from .models import Instructor
from courses.models import Course
from django.contrib.auth import get_user_model
import random
import string
import re

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

    def validate_bank_account_number(self, value):
        if value and len(value) > 20:
            raise serializers.ValidationError("Bank account number must not exceed 20 characters.")
        return value

    def create(self, validated_data):
        courses = validated_data.pop("assigned_courses", [])
        email = validated_data["email"]
        full_name = validated_data.get("full_name", "")

        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        base_username = re.sub(r'[^a-zA-Z0-9]+', '', full_name.lower()) or email.split("@")[0]
        username = base_username
        suffix = 1
        while User.objects.filter(username=username).exclude(email=email).exists():
            suffix += 1
            username = f"{base_username}{suffix}"

        user = User.objects.filter(email=email).first()

        if not user:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role="instructor"   # ✅ SET ROLE HERE
            )
        else:
            # 🔥 UPDATE ROLE IF EXISTS
            user.role = "instructor"
            user.username = username
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

        # Keep the generated password on the instance so the view can send email
        # after the DB transaction succeeds.
        instructor._generated_password = password

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

    def to_internal_value(self, data):
        data = data.copy()
        from django.core.files.base import File
        raw_doc = data.get('document', None)
        if raw_doc is not None and not isinstance(raw_doc, File):
            data.pop('document', None)
        return super().to_internal_value(data)

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

        instructor = super().update(instance, validated_data)

        # Keep auth user active state in sync with instructor record.
        if "is_active" in validated_data and instructor.user:
            user = instructor.user
            user.is_active = instructor.is_active
            user.save(update_fields=["is_active"])

        return instructor