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