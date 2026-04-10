# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import JsonResponse
from .models import Course, Task, Lesson, UserProfile
from .forms import SignUpForm, CourseForm, TaskForm, LessonForm
from .utils import update_streak, get_productivity_insights, get_notifications
from datetime import timedelta

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def dashboard(request):
    user = request.user
    tasks = Task.objects.filter(user=user)
    courses = Course.objects.filter(user=user)
    
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(completed=True).count()
    pending_tasks = tasks.filter(completed=False).count()
    overdue_tasks = tasks.filter(completed=False, deadline__lt=timezone.now().date()).count()
    
    # Course progress data for chart
    course_names = [course.name for course in courses]
    course_progress = [course.progress_percentage() for course in courses]
    # course_data = []
    # for course in courses:
    #     course_data.append({
    #         'name': course.name,
    #         'progress': course.progress_percentage()
    #     })
    
    # Task completion data
    task_completion_data = {
        
        'completed': completed_tasks,
        'pending': pending_tasks
    }
    
    # Insights
    insights = get_productivity_insights(user)
    
    # Notifications
    notifications = get_notifications(user)
    
    # Daily and Weekly Schedule
    today = timezone.now().date()
    weekly_tasks = tasks.filter(
        deadline__gte=today,
        deadline__lte=today + timedelta(days=7),
        completed=False
    ).order_by('deadline')
    
    daily_tasks = tasks.filter(deadline=today, completed=False)
    
    streak = user.userprofile.streak

    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'overdue_tasks': overdue_tasks,

        'course_names': course_names,      
        'course_progress': course_progress,
    
        # 'course_data': course_data,
        'task_completion_data': task_completion_data,
        'insights': insights,
        'notifications': notifications,
        'daily_tasks': daily_tasks,
        'weekly_tasks': weekly_tasks,
        'streak': streak,
    }
    return render(request, 'dashboard.html', context)

@login_required
def mark_task_complete(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    if request.method == 'POST':
        task.completed = not task.completed
        task.save()
        if task.completed:
            update_streak(request.user)
        messages.success(request, f'Task "{task.title}" updated.')
    return redirect('dashboard')

@login_required
def mark_lesson_complete(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, course__user=request.user)
    if request.method == 'POST':
        lesson.completed = not lesson.completed
        lesson.save()
        if lesson.completed:
            update_streak(request.user)
        messages.success(request, f'Lesson "{lesson.title}" updated.')
    return redirect('course_detail', pk=lesson.course.id)

@login_required
def lesson_delete(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, course__user=request.user)
    course_id = lesson.course.id
    if request.method == 'POST':
        lesson_title = lesson.title
        lesson.delete()
        messages.success(request, f'Lesson "{lesson_title}" has been deleted.')
    return redirect('course_detail', pk=course_id)
# Course Views
class CourseListView(ListView):
    model = Course
    template_name = 'course_list.html'
    context_object_name = 'courses'
    
    def get_queryset(self):
        return Course.objects.filter(user=self.request.user)

class CourseCreateView(CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'course_form.html'
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)   # حفظ الكورس أولاً
        
        # إنشاء الدروس تلقائياً بعد حفظ الكورس
        num_lessons = form.cleaned_data.get('number_of_lessons', 0)
        if num_lessons and num_lessons > 0:
            for i in range(1, num_lessons + 1):
                Lesson.objects.create(
                    course=self.object,
                    title=f"Lesson {i}",   
                    completed=False
                )
        return response

class CourseUpdateView(UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'course_form.html'
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # إزالة حقل عدد الدروس عند التعديل
        if 'number_of_lessons' in form.fields:
            del form.fields['number_of_lessons']
        return form
    
    def get_queryset(self):
        return Course.objects.filter(user=self.request.user)

class CourseDeleteView(DeleteView):
    model = Course
    template_name = 'course_confirm_delete.html'
    success_url = reverse_lazy('course_list')
    
    def get_queryset(self):
        return Course.objects.filter(user=self.request.user)

@login_required
def course_detail(request, pk):
    course = get_object_or_404(Course, id=pk, user=request.user)
    lessons = course.lessons.all()
    tasks = course.tasks.all()
    
    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            messages.success(request, 'Lesson added successfully!')
            return redirect('course_detail', pk=course.id)
    else:
        form = LessonForm()
    
    context = {
        'course': course,
        'lessons': lessons,
        'tasks': tasks,
        'form': form,
        'progress': course.progress_percentage()
    }
    return render(request, 'course_detail.html', context)

# Task Views
class TaskListView(ListView):
    model = Task
    template_name = 'task_list.html'
    context_object_name = 'tasks'
    
    def get_queryset(self):
        return Task.objects.filter(user=self.request.user).order_by('-priority', 'deadline')

class TaskCreateView(CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'task_form.html'
    success_url = reverse_lazy('task_list')   # أضف هذا السطر
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['course'].queryset = Course.objects.filter(user=self.request.user)
        return form

class TaskUpdateView(UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'task_form.html'
    success_url = reverse_lazy('task_list')
    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['course'].queryset = Course.objects.filter(user=self.request.user)
        return form

class TaskDeleteView(DeleteView):
    model = Task
    template_name = 'task_confirm_delete.html'
    success_url = reverse_lazy('task_list')
    
    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

# Pomodoro API (optional)
@login_required
def pomodoro_log(request):
    # Simple logging endpoint for pomodoro sessions
    if request.method == 'POST':
        # Could store pomodoro sessions in a model for analytics
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)