from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class CustomUserAdmin(UserAdmin):
    model = User

    # List view
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')

    # Edit user view
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role',)}),
    )

    # Add user view (FIXED)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )

    # # 🔥 Make email required
    # def get_form(self, request, obj=None, **kwargs):
    #     form = super().get_form(request, obj, **kwargs)
    #     form.base_fields['email'].required = True
    #     return form

    # 🔥 IMPROVEMENT → Normalize email before saving
    def save_model(self, request, obj, form, change):
        if obj.email:
            obj.email = obj.email.lower()
        super().save_model(request, obj, form, change)


admin.site.register(User, CustomUserAdmin)