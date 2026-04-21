from django.db import models
from django.conf import settings
from django.utils.text import slugify
from cloudinary_storage.storage import VideoMediaCloudinaryStorage
from django.contrib.auth import get_user_model

User = get_user_model()


class BlogCategory(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while BlogCategory.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Blog(models.Model):

    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('scheduled', 'Scheduled'),
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)

    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='blogs'
    )

    tags = models.ManyToManyField(Tag, blank=True)

    featured_image = models.ImageField(upload_to='blogs/images/', blank=True, null=True)
    video = models.FileField(upload_to='blogs/videos/', blank=True, null=True, storage=VideoMediaCloudinaryStorage())

    content = models.TextField()
    excerpt = models.TextField(blank=True, null=True)  # Short Description / Excerpt

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    publish_at = models.DateTimeField(null=True, blank=True)  # 🔥 NEW FIELD

    is_deleted = models.BooleanField(default=False)

    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Blog.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title