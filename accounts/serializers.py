from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken



User =get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role']

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):

    username_or_email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    role = serializers.ChoiceField(
        choices=["student", "instructor", "blog_admin", "admin"]
    )

    def validate(self, data):

        username_or_email = data.get("username_or_email")
        password = data.get("password")
        role = data.get("role")

        user = User.objects.filter(email=username_or_email).first()

        if not user:
            user = User.objects.filter(username=username_or_email).first()

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        user = authenticate(username=user.username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        # 🔥 ROLE VALIDATION
        if role == "admin":
            if not user.is_superuser:
                raise serializers.ValidationError("You are not an admin")
        else:
            if user.role != role:
                raise serializers.ValidationError("Incorrect role selected")

        # 🔐 FIRST LOGIN CHECK (UPDATED ✅)
        if hasattr(user, "instructor"):
            instructor = user.instructor

            if instructor.is_first_login:
                refresh = RefreshToken.for_user(user)

                return {
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": role,
                    "is_first_login": True,
                    "refresh": str(refresh),                # ✅ ADD
                    "access": str(refresh.access_token)     # ✅ ADD
                }

        # 🔥 NORMAL LOGIN
        refresh = RefreshToken.for_user(user)

        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": role,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "is_first_login": False   # ✅ CHANGED
        }

         



# class LoginSerializer(serializers.Serializer):

#     username_or_email = serializers.CharField()
#     password = serializers.CharField(write_only=True)

#     def validate(self, data):

#         username_or_email = data.get("username_or_email")
#         password = data.get("password")

#         if not username_or_email or not password:
#             raise serializers.ValidationError("Username/Email and password required")

#         # find user
#         user = User.objects.filter(email=username_or_email).first()

#         if not user:
#             user = User.objects.filter(username=username_or_email).first()

#         if not user:
#             raise serializers.ValidationError("Invalid credentials")

#         # authenticate
#         user = authenticate(username=user.username, password=password)

#         if not user:
#             raise serializers.ValidationError("Invalid credentials")

#         # detect role automatically
#         if user.is_superuser:
#             role = "admin"
#         else:
#             role = user.role

#         # generate token
#         refresh = RefreshToken.for_user(user)

#         return {
#             "user_id": user.id,
#             "username": user.username,
#             "email": user.email,
#             "role": role,
#             "refresh": str(refresh),
#             "access": str(refresh.access_token),
#         }