import os
import django
from django.core.files.uploadedfile import SimpleUploadedFile
import time

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
User = get_user_model()
from courses.models import Course, Module, Lesson, Assignment, Submission
from enrollments.models import Enrollment

def test_file_access_flow():
    client = APIClient()

    # 1. Setup participants
    instructor_user, _ = User.objects.get_or_create(username="test_instructor", email="inst@test.com", defaults={"role": "instructor"})
    student_user, _ = User.objects.get_or_create(username="test_student", email="student@test.com", defaults={"role": "student"})
    instructor_user.set_password("password")
    student_user.set_password("password")
    instructor_user.save()
    student_user.save()

    # 2. Setup Course Structure
    course = Course.objects.first()
    if not course:
        from courses.models import Category
        cat = Category.objects.create(name="Test Cat")
        course = Course.objects.create(title="Test Course", category=cat)
    
    module = Module.objects.create(course=course, title="Test Module")
    lesson = Lesson.objects.create(module=module, title="Test Lesson")

    # 3. Enroll Student
    Enrollment.objects.get_or_create(email=student_user.email, course=course, defaults={"status": "approved"})

    # 4. Instructor Uploads Assignment File (Using a valid 1x1 PNG)
    white_1x1_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n\x2e\xe4\x00\x00\x00\x00IEND\xaeB`\x82'
    dummy_img = SimpleUploadedFile("test_assignment_real.png", white_1x1_png, content_type="image/png")
    assignment = Assignment.objects.create(
        lesson=lesson,
        assignment_title="Test Assignment with File",
        file=dummy_img
    )
    print(f"Assignment created with file ID: {assignment.id}, File: {assignment.file.name}")

    # 5. Student Tries to Access Assignment File
    client.force_authenticate(user=student_user)
    access_url = f"/api/courses/files/access/?type=assignment&id={assignment.id}"
    response = client.get(access_url)
    if response.status_code == 200:
        print(f"Student successfully got signed URL for assignment: {response.data.get('signed_url', 'MISSING_URL')}")
    else:
        print(f"Student FAILED to get signed URL: {response.status_code} - {response.data}")

    # 6. Student Uploads Submission File
    dummy_submission_img = SimpleUploadedFile("student_submission_real.png", white_1x1_png, content_type="image/png")
    submit_url = f"/api/courses/assignments/{assignment.id}/submit/"
    
    response = client.post(submit_url, {
        "text_answer": "Here is my work",
        "file_upload": dummy_submission_img
    }, format='multipart')
    
    if response.status_code == 201:
        submission_id = response.data['id']
        print(f"Student successfully submitted file, Submission ID: {submission_id}")
    else:
        print(f"Student FAILED to submit file: {response.status_code} - {response.data}")
        return

    # 7. Instructor Tries to Access Student Submission File
    instructor_user.is_superuser = True 
    instructor_user.save()
    client.force_authenticate(user=instructor_user)

    access_url = f"/api/courses/files/access/?type=submission&id={submission_id}"
    response = client.get(access_url)
    if response.status_code == 200:
        print(f"Instructor successfully got signed URL for submission: {response.data.get('signed_url', 'MISSING_URL')}")
    else:
        print(f"Instructor FAILED to get signed URL: {response.status_code} - {response.data}")

if __name__ == "__main__":
    test_file_access_flow()
