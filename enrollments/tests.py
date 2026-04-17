from django.test import TestCase, override_settings
from django.core import mail

from enrollments.tasks import send_student_approval_email_sync


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class EnrollmentEmailTemplateTests(TestCase):
	def test_student_approval_email_contains_required_credentials_fields(self):
		send_student_approval_email_sync(
			name="Test Student",
			username="teststudent",
			password="Pass1234",
			course="SAP ABAP",
			email="student@example.com",
		)

		self.assertEqual(len(mail.outbox), 1)
		body = mail.outbox[0].body
		self.assertIn("Hi Test Student", body)
		self.assertIn("UserEmail: student@example.com", body)
		self.assertIn("Username: teststudent", body)
		self.assertIn("Password: Pass1234", body)
