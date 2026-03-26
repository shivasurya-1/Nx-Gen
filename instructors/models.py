from django.db import models
from django.conf import settings


from courses.models import Course
from cloudinary_storage.storage import RawMediaCloudinaryStorage


User = settings.AUTH_USER_MODEL


class Instructor(models.Model):

    user = models.OneToOneField(
    User,
    on_delete=models.CASCADE,
    null=True,     # ✅ VERY IMPORTANT
    blank=True     # ✅ VERY IMPORTANT
)

    # 🔥 Basic Info
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    email = models.EmailField(unique=True)

    # 🔥 Employee Details
    employee_id = models.CharField(max_length=50)
    date_of_joining = models.DateField()

    assigned_courses = models.ManyToManyField(Course, blank=True, related_name='instructor_assigned_courses')

    # 🔥 Academic Info
    qualification = models.CharField(max_length=200)

    EXPERIENCE_CHOICES = (
        ('Fresher', 'fresher'),
        ('1-3 Years', '1-3 years'),
        ('3+ Years', '3+ years'),
    )

    experience = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES)

    # 🔥 Bank Details
    bank_account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20)
    pan_number = models.CharField(max_length=20)
    aadhaar_number = models.CharField(max_length=20)

    # 🔥 Document Type Dropdown
    DOCUMENT_TYPE_CHOICES = (
        ('AADHAAR', 'Aadhaar'),
        ('PAN', 'PAN'),
        ('OTHER', 'Other'),
    )

    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES,
        default='AADHAAR'
    )

    # 🔥 File Upload
    document = models.FileField(
        upload_to="instructor_docs/",
        null=True,
        blank=True,
        storage=RawMediaCloudinaryStorage()
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    is_first_login = models.BooleanField(default=True)

    def __str__(self):
        return self.full_name