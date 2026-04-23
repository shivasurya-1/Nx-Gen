from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.utils import timezone

class User(AbstractUser):
    STUDENT = 'student'
    INSTRUCTOR = 'instructor'
    ADMIN = 'admin'
    BLOG_ADMIN = 'blog_admin'

    ROLE_CHOICES = (
        (STUDENT, 'Student'),
        (INSTRUCTOR, 'Instructor'),
        (ADMIN, 'Admin'),
        (BLOG_ADMIN, 'Blog Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    email = models.EmailField(unique=True,blank=False,null=False)

    def __str__(self):
        return self.username

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    phone = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    is_first_login = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class PasswordResetToken(models.Model):
    """Model to store OTP and reset tokens for password reset flow"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='password_reset')
    otp = models.CharField(max_length=6)
    reset_token = models.CharField(max_length=255, unique=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"Reset token for {self.user.email}"

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_otp_valid(self, otp):
        return self.otp == otp and not self.is_expired()