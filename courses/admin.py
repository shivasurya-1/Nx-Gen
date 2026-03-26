from django.contrib import admin
from .models import Category, Course, CourseContent, Lesson, Module, Submission


admin.site.register(Category)
admin.site.register(Course)
admin.site.register(CourseContent)
admin.site.register(Module)
admin.site.register(Lesson)
admin.site.register(Submission)