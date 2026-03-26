from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, LoginSerializer
from .models import User
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)



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

        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not current_password or not new_password or not confirm_password:
            return Response({"error": "All fields are required"}, status=400)

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

        return Response({
            "message": "Password changed successfully"
        }, status=200)

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