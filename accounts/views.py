from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    RegisterSerializer, 
    LoginSerializer,
    ForgotPasswordRequestSerializer,
    ForgotPasswordVerifyOTPSerializer,
    ForgotPasswordResetSerializer
)
from .models import User, PasswordResetToken
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
import random
import uuid
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                return Response(
                    {
                        "message": "User registered successfully",
                        "user": serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {"error": "Failed to register user", "details": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LoginView(APIView):

    def post(self, request):

        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    








class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        user = request.user

        current_password = request.data.get("current_password") or request.data.get("old_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not current_password or not new_password or not confirm_password:
            return Response({"error": "All credentials are required"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(current_password):
            return Response({"error": "Current password is incorrect"}, status=400)

        if new_password != confirm_password:
            return Response({"error": "Passwords do not match"}, status=400)

        if current_password == new_password:
            return Response({"error": "New password must be different"}, status=400)

        # 🔥 SET NEW PASSWORD
        user.set_password(new_password)
        user.save()

        # 🔥 UPDATE FIRST LOGIN FLAG
        if hasattr(user, "instructor"):
            instructor = user.instructor
            instructor.is_first_login = False   # ✅ IMPORTANT
            instructor.save()

        if hasattr(user, "student_profile"):
            student_profile = user.student_profile
            if student_profile.is_first_login:
                student_profile.is_first_login = False
                student_profile.save(update_fields=["is_first_login"])

        return Response({
            "message": "Password changed successfully"
        }, status=status.HTTP_200_OK)

# class StudentLoginView(APIView):
#     def post(self, request):
#         serializer = LoginSerializer(data=request.data)
#         if serializer.is_valid():
#             user_role = serializer.validated_data['role']
#             if user_role != 'student':
#                 return Response(
#                     {"error": "You are not a student"},
#                     status=status.HTTP_403_FORBIDDEN
#                 )
#             return Response(serializer.validated_data)
#         return Response(serializer.errors, status=400)


# class InstructorLoginView(APIView):
#     def post(self, request):
#         serializer = LoginSerializer(data=request.data)
#         if serializer.is_valid():
#             user_role = serializer.validated_data['role']
#             if user_role != 'instructor':
#                 return Response(
#                     {"error": "You are not an instructor"},
#                     status=status.HTTP_403_FORBIDDEN
#                 )
#             return Response(serializer.validated_data)
#         return Response(serializer.errors, status=400)

# class AdminLoginView(APIView):
#     # def post(self, request):
#     #     serializer = AdminLoginSerializer(data=request.data)
#     #     if serializer.is_valid():
#     #         user_role = serializer.validated_data['role']
#     #         if user_role != 'admin':
#     #             return Response(
#     #                 {"error": "You are not an admin"},
#     #                     status=status.HTTP_403_FORBIDDEN
#     #                 )
#     #         return Response(serializer.validated_data)
#     #     return Response(serializer.errors, status=400)
#     def post(self, request):
#         serializer = AdminLoginSerializer(data=request.data)

#         if serializer.is_valid():
#             return Response(serializer.validated_data, status=status.HTTP_200_OK)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
from .models import StudentProfile
class StudentProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            profile = request.user.student_profile
            return Response({
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                'phone': profile.phone,
                'location': profile.location,
                'bio': profile.bio
            })
        except Exception:
            return Response({
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                'phone': '',
                'location': '',
                'bio': ''
            })
    def patch(self, request):
        user = request.user
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.save()
        profile, created = StudentProfile.objects.get_or_create(user=user)
        profile.phone = request.data.get('phone', profile.phone)
        profile.location = request.data.get('location', profile.location)
        profile.bio = request.data.get('bio', profile.bio)
        profile.save()
        return Response({'message': 'Profile updated successfully'})


# ==================== FORGOT PASSWORD FLOW ====================

class ForgotPasswordRequestView(APIView):
    """
    Request password reset - generates OTP and sends via email
    """
    def post(self, request):
        serializer = ForgotPasswordRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)

            # Generate 6-digit OTP
            otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])

            # Generate reset token
            reset_token = str(uuid.uuid4())

            # Create or update password reset record
            expires_at = timezone.now() + timedelta(minutes=10)  # OTP valid for 10 minutes
            password_reset, created = PasswordResetToken.objects.get_or_create(
                user=user,
                defaults={
                    'otp': otp,
                    'reset_token': reset_token,
                    'expires_at': expires_at
                }
            )

            if not created:
                password_reset.otp = otp
                password_reset.reset_token = reset_token
                password_reset.expires_at = expires_at
                password_reset.is_verified = False
                password_reset.save()

            # Send OTP via email
            try:
                send_mail(
                    subject="Password Reset Request - Your OTP",
                    message=f"""Hello {user.first_name or user.username},

You requested to reset your password. Your One-Time Password (OTP) is:

{otp}

This OTP is valid for 10 minutes. Do not share this OTP with anyone.

If you didn't request this, please ignore this email.

Best regards,
NxGen Team""",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as e:
                return Response(
                    {"error": "Failed to send OTP email", "details": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response(
                {
                    "message": "OTP sent successfully to your registered email",
                    "email": email
                },
                status=status.HTTP_200_OK
            )

        except User.DoesNotExist:
            # For security, don't reveal that email doesn't exist
            return Response(
                {"message": "If the email exists, OTP will be sent shortly"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": "Failed to process request", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ForgotPasswordVerifyOTPView(APIView):
    """
    Verify OTP - returns reset token if valid
    """
    def post(self, request):
        serializer = ForgotPasswordVerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']

            user = User.objects.get(email=email)
            password_reset = user.password_reset

            if password_reset.is_otp_valid(otp):
                password_reset.is_verified = True
                password_reset.save()

                return Response(
                    {
                        "message": "OTP verified successfully",
                        "reset_token": password_reset.reset_token
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": "Invalid or expired OTP"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": "Failed to verify OTP", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ForgotPasswordResetView(APIView):
    """
    Reset password - update with new password after OTP verification
    """
    def post(self, request):
        serializer = ForgotPasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            email = serializer.validated_data['email']
            new_password = serializer.validated_data['new_password']

            user = User.objects.get(email=email)
            password_reset = user.password_reset

            # Verify OTP one more time
            if not password_reset.is_verified:
                return Response(
                    {"error": "OTP not verified. Please verify OTP first."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update password
            user.set_password(new_password)
            user.save()

            # Clear password reset record
            password_reset.delete()

            return Response(
                {"message": "Password reset successfully. You can now login with your new password."},
                status=status.HTTP_200_OK
            )

        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": "Failed to reset password", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
