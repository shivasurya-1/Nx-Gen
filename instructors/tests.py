from django.core import mail
from django.test import TestCase, override_settings

from instructors.tasks import send_instructor_credentials_email_sync


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class InstructorEmailTemplateTests(TestCase):
	def test_instructor_credentials_email_contains_required_fields(self):
		send_instructor_credentials_email_sync(
			email="instructor@example.com",
			name="Instructor Name",
			username="instructorname",
			password="Pass1234",
		)

		self.assertEqual(len(mail.outbox), 1)
		body = mail.outbox[0].body
		self.assertIn("Hi Instructor Name", body)
		self.assertIn("UserEmail: instructor@example.com", body)
		self.assertIn("Username: instructorname", body)
		self.assertIn("Password: Pass1234", body)
