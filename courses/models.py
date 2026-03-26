from django.db import models
from django.conf import settings
from cloudinary_storage.storage import RawMediaCloudinaryStorage

User = settings.AUTH_USER_MODEL


class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="courses"
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class CourseContent(models.Model):
    """Legacy model — kept for backward compatibility."""
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="contents"
    )
    title = models.CharField(max_length=300)
    description = models.TextField()

    def __str__(self):
        return self.title


class Module(models.Model):
    """
    A module belongs directly to a Course and is categorised
    into one of two sections: Training or Industry Readiness.
    """
    SECTION_TYPES = (
        ("training", "Training"),
        ("industry_readiness", "Industry Readiness"),
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="modules"
    )
    section_type = models.CharField(
        max_length=50,
        choices=SECTION_TYPES,
        default="training"
    )
    title = models.CharField(max_length=255)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"[{self.get_section_type_display()}] {self.title}"


class Lesson(models.Model):
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="lessons"
    )
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    file = models.FileField(upload_to="lesson_files/", null=True, blank=True, storage=RawMediaCloudinaryStorage())
    video_url = models.URLField(blank=True, null=True)
    resource_title = models.CharField(max_length=255, blank=True)
    resource_link = models.URLField(blank=True)
    
    # 🔥 Assignment fields merged
    assignment_title = models.CharField(max_length=255, blank=True)
    assignment_description = models.TextField(blank=True)
    assignment_due_date = models.DateTimeField(null=True, blank=True)

    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class Submission(models.Model):
    STATUS_CHOICES = (
        ("submitted", "Submitted"),
    )

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="submissions",
        null=True,
        blank=True
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="course_submissions"
    )
    text_answer = models.TextField(blank=True)
    file_upload = models.FileField(upload_to="submissions/", null=True, blank=True, storage=RawMediaCloudinaryStorage())
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="submitted")
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('lesson', 'student')

    def __str__(self):
        lesson_title = self.lesson.title if self.lesson else "No Lesson"
        return f"{self.student.email} - {lesson_title}"
