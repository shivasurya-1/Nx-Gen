import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()
from courses.models import Course, Module, Lesson, Assignment, Category

def test_assignments():
    client = APIClient()
    
    # 1. Create a superuser for testing
    user, created = User.objects.get_or_create(email="admin@test.com", defaults={"role": "admin", "is_superuser": True, "is_staff": True})
    if not created:
        user.is_superuser = True
        user.role = "admin"
        user.save()
    client.force_authenticate(user=user)

    # 2. Set up base data
    category, _ = Category.objects.get_or_create(name="Test Category", slug="test-cat")
    course, _ = Course.objects.get_or_create(title="Test Course", defaults={"category": category, "price": 0})
    module, _ = Module.objects.get_or_create(title="Test Module", defaults={"course": course})
    lesson, _ = Lesson.objects.get_or_create(title="Test Lesson", defaults={"module": module})

    # Clear existing assignments for this lesson to start fresh
    lesson.assignments.all().delete()
    print(f"Testing for Lesson: {lesson.title} (ID: {lesson.id})")

    # 3. Create 5 assignments via API
    url = f"/api/courses/modules/{module.id}/lessons/{lesson.id}/assignment/"
    for i in range(1, 6):
        response = client.post(url, {"assignment_title": f"Assignment {i}", "assignment_description": f"Desc {i}"})
        if response.status_code == 201:
            print(f"Successfully created assignment {i}")
        else:
            print(f"Failed to create assignment {i}: {response.data}")

    # 4. Attempt to create a 6th assignment (Should fail)
    response = client.post(url, {"assignment_title": "Assignment 6", "assignment_description": "Should fail"})
    if response.status_code == 400 and "error" in response.data:
        print("Correctly blocked 6th assignment creation")
    else:
        print(f"Unexpected behavior on 6th assignment: {response.status_code} - {response.data}")

    # 5. Verify listing
    response = client.get(url)
    if response.status_code == 200 and len(response.data) == 5:
        print(f"Correctly returned 5 assignments in GET")
    else:
        print(f"Failed to list assignments: {response.status_code} - {response.data}")

    # 6. Test Detail View
    if len(response.data) > 0:
        first_id = response.data[0]['id']
        detail_url = f"/api/courses/assignments/{first_id}/"
        response = client.get(detail_url)
        if response.status_code == 200 and response.data['assignment_title'] == "Assignment 1":
            print(f"Successfully retrieved detail for Assignment 1")
        else:
            print(f"Failed detail view: {response.status_code} - {response.data}")

if __name__ == "__main__":
    test_assignments()
