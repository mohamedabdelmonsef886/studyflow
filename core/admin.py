# Register your models here.
from django.contrib import admin
from .models import UserProfile, Course, Lesson, Task

admin.site.register(UserProfile)
admin.site.register(Course)
admin.site.register(Lesson)
admin.site.register(Task)