from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Course, Task, Lesson
from datetime import date
class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class CourseForm(forms.ModelForm):
    number_of_lessons = forms.IntegerField(
    min_value=0, 
    required=False, 
    label="Number of lessons",
    help_text="empty"
    )
    class Meta:
        model = Course
        fields = ['name', 'description', 'number_of_lessons']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['course', 'title', 'description', 'priority', 'start_date', 'deadline']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['deadline'].initial = date.today()
class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title']