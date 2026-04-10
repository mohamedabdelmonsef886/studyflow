from django.utils import timezone
from .models import Task, Lesson
from datetime import timedelta

def update_streak(user):
    profile = user.userprofile
    today = timezone.now().date()
    
    if profile.last_activity_date == today:
        return
    
    if profile.last_activity_date == today - timedelta(days=1):
        profile.streak += 1
    else:
        profile.streak = 1
    
    profile.last_activity_date = today
    profile.save()

def get_productivity_insights(user):
    tasks = Task.objects.filter(user=user)
    completed_tasks = tasks.filter(completed=True)
    total_tasks = tasks.count()
    
    if total_tasks == 0:
        return {
            'status': 'No tasks yet',
            'on_track': False,
            'on_time_percentage': 0,
            'estimated_days': 'N/A'
        }
    
    # Calculate on-time completion percentage
    on_time_count = 0
    for task in completed_tasks:
        if task.completed_date and task.deadline:
            if task.completed_date.date() <= task.deadline:
                on_time_count += 1
    
    on_time_percentage = (on_time_count / completed_tasks.count() * 100) if completed_tasks.count() > 0 else 0
    on_track = on_time_percentage >= 70
    
    # Calculate average completion rate (tasks per day in last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_completions = completed_tasks.filter(completed_date__gte=thirty_days_ago)
    
    if recent_completions.count() > 0:
        days_active = recent_completions.values('completed_date__date').distinct().count()
        avg_rate = recent_completions.count() / max(days_active, 1)
        pending_tasks = tasks.filter(completed=False).count()
        estimated_days = round(pending_tasks / avg_rate) if avg_rate > 0 else 'N/A'
    else:
        estimated_days = 'N/A'
    
    return {
        'status': 'On Track!' if on_track else 'Behind Schedule',
        'on_track': on_track,
        'on_time_percentage': round(on_time_percentage, 1),
        'estimated_days': estimated_days
    }

def get_notifications(user):
    today = timezone.now().date()
    tasks = Task.objects.filter(user=user, completed=False)
    
    overdue_tasks = tasks.filter(deadline__lt=today)
    due_soon_tasks = tasks.filter(deadline__gte=today, deadline__lte=today + timedelta(days=2))
    
    return {
        'overdue': overdue_tasks,
        'due_soon': due_soon_tasks
    }