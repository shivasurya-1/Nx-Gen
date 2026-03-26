from django.contrib import admin
from .models import Enrollment




class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        'id',   # ✅ ADD THIS
        'name',
        'email',
        'course',
        'status',
        'is_active',
        'created_at'
    )
# Register your models here.
admin.site.register(Enrollment, EnrollmentAdmin)