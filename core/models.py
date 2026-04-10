# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Course(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('course_detail', args=[self.id])

    def total_lessons(self):
        return self.lessons.count()

    def completed_lessons(self):
        return self.lessons.filter(completed=True).count()

    def progress_percentage(self):
        total = self.total_lessons()
        if total == 0:
            return 0
        return int((self.completed_lessons() / total) * 100)

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    completed_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.completed and not self.completed_date:
            self.completed_date = timezone.now()
        elif not self.completed:
            self.completed_date = None
        super().save(*args, **kwargs)

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    start_date = models.DateField(default=timezone.now)
    deadline = models.DateField()
    completed = models.BooleanField(default=False)
    completed_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def is_overdue(self):
        if not self.completed and self.deadline < timezone.now().date():
            return True
        return False

    def is_due_soon(self):
        if not self.completed:
            days_until = (self.deadline - timezone.now().date()).days
            return 0 <= days_until <= 2
        return False

    def save(self, *args, **kwargs):
        if self.completed and not self.completed_date:
            self.completed_date = timezone.now()
        elif not self.completed:
            self.completed_date = None
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('task_list')
