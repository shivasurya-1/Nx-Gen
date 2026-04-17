from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from courses.models import Batch, Category, Course, Lesson, Module
from enrollments.models import Enrollment
from instructors.models import Instructor


User = get_user_model()


class AssignmentScopeRegressionTests(TestCase):
	def setUp(self):
		self.client = APIClient()

		self.category = Category.objects.create(name="SAP", slug="sap")
		self.course = Course.objects.create(
			category=self.category,
			title="SAP ABAP",
			description="Course",
			price=Decimal("1000.00"),
			is_active=True,
		)

		self.instructor_user_1 = User.objects.create_user(
			username="inst1",
			email="inst1@example.com",
			password="pass12345",
			role="instructor",
		)
		self.instructor_user_2 = User.objects.create_user(
			username="inst2",
			email="inst2@example.com",
			password="pass12345",
			role="instructor",
		)

		self.instructor_1 = Instructor.objects.create(
			user=self.instructor_user_1,
			full_name="Instructor One",
			phone="9999999991",
			email="inst1@example.com",
			experience="1-3 Years",
			is_active=True,
		)
		self.instructor_2 = Instructor.objects.create(
			user=self.instructor_user_2,
			full_name="Instructor Two",
			phone="9999999992",
			email="inst2@example.com",
			experience="1-3 Years",
			is_active=True,
		)
		self.instructor_1.assigned_courses.add(self.course)
		self.instructor_2.assigned_courses.add(self.course)

		self.student_user_1 = User.objects.create_user(
			username="student1",
			email="student1@example.com",
			password="pass12345",
			role="student",
		)
		self.student_user_2 = User.objects.create_user(
			username="student2",
			email="student2@example.com",
			password="pass12345",
			role="student",
		)

		for student in (self.student_user_1, self.student_user_2):
			Enrollment.objects.create(
				name=student.username,
				email=student.email,
				phone="9000000000",
				course=self.course,
				course_type="Training",
				qualification="Graduate",
				current_status="Student",
				preferred_mode="Online",
				preferred_timing="Morning",
				experience_level="Beginner",
				terms_accepted=True,
				status="approved",
			)

		self.batch_1 = Batch.objects.create(
			name="Batch A",
			course=self.course,
			instructor=self.instructor_1,
			is_active=True,
		)
		self.batch_2 = Batch.objects.create(
			name="Batch B",
			course=self.course,
			instructor=self.instructor_2,
			is_active=True,
		)
		self.batch_1.students.add(self.student_user_1)
		self.batch_2.students.add(self.student_user_2)

		self.module_1 = Module.objects.create(
			course=self.course,
			created_by=self.instructor_1,
			section_type="training",
			title="Module Inst1",
			order=1,
		)
		self.module_2 = Module.objects.create(
			course=self.course,
			created_by=self.instructor_2,
			section_type="training",
			title="Module Inst2",
			order=2,
		)

		self.lesson_1 = Lesson.objects.create(
			module=self.module_1,
			title="Lesson One",
			assignment_title="A1",
			assignment_description="Desc",
			order=1,
		)
		self.lesson_2 = Lesson.objects.create(
			module=self.module_2,
			title="Lesson Two",
			assignment_title="A2",
			assignment_description="Desc",
			order=1,
		)

	def test_student_assignment_list_is_scoped_to_batch_instructor(self):
		self.client.force_authenticate(user=self.student_user_1)
		response = self.client.get("/api/courses/my-assignments/")

		self.assertEqual(response.status_code, 200)
		lesson_ids = {item["assignment"]["id"] for item in response.data}
		self.assertIn(self.lesson_1.id, lesson_ids)
		self.assertNotIn(self.lesson_2.id, lesson_ids)

	def test_assignment_status_is_scoped_to_instructor_batch_students(self):
		self.client.force_authenticate(user=self.instructor_user_1)
		response = self.client.get(
			f"/api/courses/modules/{self.module_1.id}/lessons/{self.lesson_1.id}/assignment/status/"
		)

		self.assertEqual(response.status_code, 200)
		student_ids = {item["student_id"] for item in response.data}
		self.assertIn(self.student_user_1.id, student_ids)
		self.assertNotIn(self.student_user_2.id, student_ids)

	def test_student_cannot_submit_assignment_outside_batch_scope(self):
		self.client.force_authenticate(user=self.student_user_2)
		response = self.client.post(
			f"/api/courses/modules/{self.module_1.id}/lessons/{self.lesson_1.id}/assignment/submit/",
			{"text_answer": "My answer"},
			format="multipart",
		)

		self.assertEqual(response.status_code, 403)
		self.assertIn("not assigned", str(response.data).lower())

	def test_lesson_patch_ignores_non_file_string_payload(self):
		self.client.force_authenticate(user=self.instructor_user_1)
		response = self.client.patch(
			f"/api/courses/modules/{self.module_1.id}/lessons/{self.lesson_1.id}/",
			{"title": "Updated Lesson", "file": "https://example.com/old-file.pdf"},
			format="multipart",
		)

		self.assertEqual(response.status_code, 200)
		self.lesson_1.refresh_from_db()
		self.assertEqual(self.lesson_1.title, "Updated Lesson")
