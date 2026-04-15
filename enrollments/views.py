from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.conf import settings
import random
import string
from .permissions import IsAdminOnly
from .tasks import (
    send_admin_enrollment_email_sync,
    send_student_approval_email_sync,
    send_student_rejection_email_sync,
)
import hmac
import hashlib
from django.utils import timezone
from .models import Enrollment
from .serializers import EnrollmentSerializer
from accounts.models import StudentProfile


import razorpay




User = get_user_model()


# ---------------- ENROLL ---------------- #

class EnrollView(APIView):

    def post(self, request):

        serializer = EnrollmentSerializer(data=request.data)

        if serializer.is_valid():
            try:
                enrollment = serializer.save()

                email_warning = None
                try:
                    send_admin_enrollment_email_sync(
                        enrollment.name,
                        enrollment.email,
                        enrollment.course.title,
                        enrollment.phone
                    )
                except Exception as email_error:
                    email_warning = f"Enrollment created, but admin notification email failed: {str(email_error)}"

                payload = {
                    "message": "Enrollment successful",
                    "enrollment_id": enrollment.id,
                    "redirect": "payment"
                }

                if email_warning:
                    payload["warning"] = email_warning

                return Response(payload, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    {"error": "Failed to create enrollment", "details": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

   

    
# ---------------- LIST ---------------- #

class EnrollmentListView(APIView):
    def get(self, request):
        enrollments = Enrollment.objects.all().order_by("-created_at")
        serializer = EnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)


# ---------------- APPROVE ---------------- #

class ApproveEnrollmentView(APIView):
    permission_classes = [IsAdminOnly]
    def post(self, request, id):
        try:
            enrollment = Enrollment.objects.get(id=id)
        except Enrollment.DoesNotExist:
            return Response({"error": "Enrollment not found"}, status=status.HTTP_404_NOT_FOUND)

        # ✅ Already approved check
        if enrollment.status == "approved":
            return Response({"message": "Already approved"}, status=status.HTTP_200_OK)

        try:
            # Reuse existing user if present, but issue fresh temporary credentials.
            user = User.objects.filter(email=enrollment.email).first()
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

            if not user:
                username = enrollment.email.split("@")[0]
                if User.objects.filter(username=username).exists():
                    username = username + str(random.randint(10, 99))
                user = User.objects.create_user(
                    username=username,
                    email=enrollment.email,
                    password=temp_password,
                    role="student"
                )
            else:
                user.role = "student"
                user.set_password(temp_password)

            user.is_active = True
            user.save()

            student_profile, _ = StudentProfile.objects.get_or_create(user=user)
            student_profile.is_first_login = True
            student_profile.save(update_fields=["is_first_login"])

            enrollment.status = "approved"
            enrollment.is_active = True
            enrollment.save()

            email_warning = None
            try:
                send_student_approval_email_sync(
                    enrollment.name,
                    user.username,
                    temp_password,
                    enrollment.course.title,
                    enrollment.email
                )
            except Exception as email_error:
                email_warning = f"Enrollment approved, but student email failed: {str(email_error)}"

            payload = {"message": "Enrollment approved successfully."}
            if email_warning:
                payload["warning"] = email_warning
            else:
                payload["message"] = "Enrollment approved successfully. Confirmation email sent to student."

            return Response(payload, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "Failed to approve enrollment", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ---------------- REJECT ---------------- #

class RejectEnrollmentView(APIView):
    permission_classes = [IsAdminOnly]

    def post(self, request, id):
        try:
            enrollment = Enrollment.objects.get(id=id)
        except Enrollment.DoesNotExist:
            return Response({"error": "Enrollment not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            # ✅ Check if already rejected
            if enrollment.status == "rejected":
                return Response({"message": "Already rejected"}, status=status.HTTP_200_OK)

            enrollment.status = "rejected"
            enrollment.save()

            email_warning = None
            try:
                send_student_rejection_email_sync(
                    enrollment.name,
                    enrollment.course.title,
                    enrollment.email
                )
            except Exception as email_error:
                email_warning = f"Enrollment rejected, but student email failed: {str(email_error)}"

            payload = {"message": "Enrollment rejected successfully."}
            if email_warning:
                payload["warning"] = email_warning
            else:
                payload["message"] = "Enrollment rejected successfully. Student has been notified."

            return Response(payload, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "Failed to reject enrollment", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )








class CreateOrderView(APIView):

    def post(self, request):
        amount = request.data.get("amount")  # in rupees

        client = razorpay.Client(auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        ))

        order = client.order.create({
            "amount": int(amount) * 100,  # convert to paisa
            "currency": "INR",
            "payment_capture": 1
        })

        return Response({
            "order_id": order["id"],
            "amount": order["amount"],
            "key": settings.RAZORPAY_KEY_ID
        })





class VerifyPaymentView(APIView):

    def post(self, request):
        data = request.data

        razorpay_order_id = data.get("razorpay_order_id")
        razorpay_payment_id = data.get("razorpay_payment_id")
        razorpay_signature = data.get("razorpay_signature")
        enrollment_id = data.get("enrollment_id")

        # 🔒 Generate signature
        generated_signature = hmac.new(
            bytes(settings.RAZORPAY_KEY_SECRET, 'utf-8'),
            bytes(f"{razorpay_order_id}|{razorpay_payment_id}", 'utf-8'),
            hashlib.sha256
        ).hexdigest()

        # ✅ Verify payment
        if generated_signature == razorpay_signature:

            try:
                enrollment = Enrollment.objects.get(id=enrollment_id)
            except Enrollment.DoesNotExist:
                return Response({"error": "Enrollment not found"}, status=404)

            # 🔥 Update enrollment
            enrollment.payment_status = "paid"
            enrollment.razorpay_order_id = razorpay_order_id
            enrollment.razorpay_payment_id = razorpay_payment_id
            enrollment.save()

            return Response({
                "message": "Payment verified & enrollment updated"
            })

        else:
            return Response({
                "error": "Payment verification failed"
            }, status=400)
from rest_framework.permissions import IsAuthenticated
from .serializers import StudentEnrolledCourseSerializer
from learning.models import LessonProgress
from courses.models import Batch

class StudentCoursesView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        email = request.user.email
        enrollments = Enrollment.objects.filter(email=email, status='approved', is_active=True)
        serializer = StudentEnrolledCourseSerializer(enrollments, many=True, context={'request': request})
        return Response(serializer.data)

class StudentDashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        email = request.user.email
        enrolled_count = Enrollment.objects.filter(email=email, status='approved', is_active=True).count()
        completed_lessons = LessonProgress.objects.filter(student=request.user, completed=True).count()
        
        active_batches = Batch.objects.filter(students=request.user, is_live_class_active=True)
        active_live_classes = []
        for b in active_batches:
            active_live_classes.append({
                'course_title': b.course.title,
                'batch_name': b.name,
                'live_link': b.live_link
            })
            
        return Response({
            'enrolled_courses_count': enrolled_count,
            'completed_lessons_count': completed_lessons,
            'next_live_session': 'Saturday, 10:00 AM',
            'active_live_classes': active_live_classes
        })