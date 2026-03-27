from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from courses.models import Lesson
from enrollments.models import Enrollment
from courses.serializers import LessonSerializer

from .models import LessonProgress

# Create your views here.
class SaveProgressView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        lesson_id = request.data.get("lesson_id")
        seconds = request.data.get("seconds")

        lesson = Lesson.objects.get(id=lesson_id)

        progress, created = LessonProgress.objects.get_or_create(
            student=request.user,
            lesson=lesson
        )

        progress.watched_seconds = seconds

        if seconds >= lesson.duration * 0.9:
            progress.completed = True

        progress.save()

        return Response({"message": "progress saved"})
    
class CourseProgressView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):

        total_lessons = Lesson.objects.filter(
            module__course_id=course_id
        ).count()

        completed = LessonProgress.objects.filter(
            student=request.user,
            lesson__module__course_id=course_id,
            completed=True
        ).count()

        progress = 0

        if total_lessons > 0:
            progress = (completed / total_lessons) * 100

        return Response({
            "total_lessons": total_lessons,
            "completed_lessons": completed,
            "progress_percentage": round(progress, 2)
        })
    

class LessonProgressView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, lesson_id):

        progress = LessonProgress.objects.filter(
            student=request.user,
            lesson_id=lesson_id
        ).first()

        if not progress:
            return Response({"watched_seconds": 0})

        return Response({
            "watched_seconds": progress.watched_seconds
        })
    

class LessonDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, lesson_id):

        lesson = Lesson.objects.get(id=lesson_id)

        course = lesson.module.course

        enrolled = Enrollment.objects.filter(
            student=request.user,
            course=course,
            status="approved"
        ).exists()

        if not enrolled:
            return Response(
                {"error": "Not enrolled"},
                status=403
            )

        serializer = LessonSerializer(lesson)

        return Response(serializer.data)
class RecentProgressView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        recent = LessonProgress.objects.filter(student=request.user).order_by('-updated_at')[:5]
        data = []
        for p in recent:
            data.append({
                'lesson_title': p.lesson.title,
                'course_title': p.lesson.module.course.title,
                'completed': p.completed,
                'updated_at': p.updated_at
            })
        return Response(data)
