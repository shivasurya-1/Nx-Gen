from django.contrib import admin
from .models import Instructor


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):

    # 🔥 List view
    list_display = (
        "id",
        "full_name",
        "phone",
        "employee_id",
        "is_active",
        "created_at"
    )

    # 🔍 Search
    search_fields = ("full_name", "phone", "employee_id")

    # 🔽 Filters
    list_filter = ("is_active", "experience")

    # 🔥 Multi-select courses
    filter_horizontal = ("assigned_courses",)

    # 🔥 Editable in list (optional)
    list_editable = ("is_active",)

    # 🔥 Ordering
    ordering = ("-created_at",)

    def save_model(self, request, obj, form, change):

        if obj.user:
            obj.user.role = "instructor"   # ✅ AUTO SET ROLE
            obj.user.save()

        super().save_model(request, obj, form, change)

    # 🔒 OPTIONAL: Only admin can add
    def has_add_permission(self, request):
        return request.user.is_superuser

    # 🔒 OPTIONAL: Only admin can delete
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser