from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.conf import settings
import random
import string
from enrollments.tasks import send_admin_enrollment_email
from .permissions import IsAdminOnly
from .tasks import send_admin_enrollment_email, send_student_approval_email, send_student_rejection_email
import hmac
import hashlib
from django.utils import timezone
from .models import Enrollment
from .serializers import EnrollmentSerializer


import razorpay




User = get_user_model()


# ---------------- ENROLL ---------------- #

class EnrollView(APIView):

    def post(self, request):

        serializer = EnrollmentSerializer(data=request.data)

        if serializer.is_valid():
            enrollment = serializer.save()

            # 🔥 EMAIL TO ADMIN (YOUR EXISTING LOGIC)
            

            send_admin_enrollment_email.delay(
    enrollment.name,
    enrollment.email,
    enrollment.course.title,
    enrollment.phone
)

            return Response({
                "message": "Enrollment successful",
                "enrollment_id": enrollment.id,
                "redirect": "payment"
            })

        return Response(serializer.errors, status=400)

   

    
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
            return Response({"error": "Not found"}, status=404)

        # ✅ Already approved check
        if enrollment.status == "approved":
            return Response({"message": "Already approved"}, status=400)

        # ✅ FIX: reuse existing user
        user = User.objects.filter(email=enrollment.email).first()

        if not user:
            # 🔥 Generate username
            username = enrollment.email.split("@")[0]

            # Avoid duplicate username
            if User.objects.filter(username=username).exists():
                username = username + str(random.randint(10, 99))

            # 🔥 Generate password
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

            # 🔥 Create user
            user = User.objects.create_user(
                username=username,
                email=enrollment.email,
                password=password,
                role="student"
            )

            user.is_active = True
            user.save()

            send_password = password  # only for new user

        else:
            # 🔥 Existing user → no new password
            send_password = "Use your existing password"

        # 🔥 Update enrollment
        enrollment.status = "approved"
        enrollment.is_active = True
        enrollment.save()

        # 🔥 EMAIL TO STUDENT
        

        send_student_approval_email.delay(
    enrollment.name,
    user.username,
    send_password,
    enrollment.course.title,
    enrollment.email
)

        return Response({"message": "Approved + email sent"})


# ---------------- REJECT ---------------- #

class RejectEnrollmentView(APIView):

    def post(self, request, id):
        try:
            enrollment = Enrollment.objects.get(id=id)
        except Enrollment.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

        enrollment.status = "rejected"
        enrollment.save()

        # 🔥 EMAIL TO STUDENT
        

        send_student_rejection_email.delay(
    enrollment.name,
    enrollment.course.title,
    enrollment.email
)

        return Response({"message": "Enrollment rejected"})








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