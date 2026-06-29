"""
Dashboard app: aggregates the current user's tasks into the counters
and chart datasets shown on the main dashboard page. Every query is
scoped to `request.user`, and the same aggregation function powers
both the initial page render and the AJAX refresh endpoint, so the
numbers can never drift between the two.
"""
import calendar
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from core.models import ActivityLog
from tasks.models import Task


def _build_dashboard_data(user):
    tasks = Task.objects.filter(user=user)

    total = tasks.count()
    completed = tasks.filter(status=Task.Status.COMPLETED).count()
    in_progress = tasks.filter(status=Task.Status.IN_PROGRESS).count()
    pending = tasks.filter(status=Task.Status.PENDING).count()
    high_priority = tasks.filter(priority=Task.Priority.HIGH).exclude(status=Task.Status.COMPLETED).count()
    overdue = sum(1 for t in tasks.exclude(status=Task.Status.COMPLETED) if t.is_overdue)

    completion_rate = round((completed / total) * 100, 1) if total else 0.0

    # --- Pie chart: tasks by status ---
    status_counts = {
        'Pending': pending,
        'In Progress': in_progress,
        'Completed': completed,
    }

    # --- Bar chart: tasks by priority ---
    priority_qs = tasks.values('priority').annotate(count=Count('id'))
    priority_map = {row['priority']: row['count'] for row in priority_qs}
    priority_counts = {
        'Low': priority_map.get(Task.Priority.LOW, 0),
        'Medium': priority_map.get(Task.Priority.MEDIUM, 0),
        'High': priority_map.get(Task.Priority.HIGH, 0),
    }

    # --- Line chart: tasks created per month (last 6 months) ---
    now = timezone.localtime()
    months = []
    month_counts = []
    for i in range(5, -1, -1):
        year = now.year
        month = now.month - i
        while month <= 0:
            month += 12
            year -= 1
        label = f"{calendar.month_abbr[month]} {year}"
        count = tasks.filter(created_at__year=year, created_at__month=month).count()
        months.append(label)
        month_counts.append(count)

    # --- Recent activity feed ---
    recent_activity = list(
        ActivityLog.objects.filter(user=user).values(
            'action', 'description', 'icon', 'created_at'
        )[:8]
    )
    for entry in recent_activity:
        entry['created_at'] = entry['created_at'].isoformat()

    # --- Upcoming deadlines (next 7 days, not completed) ---
    soon = now + timedelta(days=7)
    upcoming = list(
        tasks.exclude(status=Task.Status.COMPLETED)
        .filter(deadline__isnull=False, deadline__lte=soon)
        .order_by('deadline')
        .values('id', 'title', 'deadline', 'priority')[:5]
    )
    for task in upcoming:
        task['deadline'] = task['deadline'].isoformat()

    return {
        'counters': {
            'total': total,
            'completed': completed,
            'pending': pending,
            'in_progress': in_progress,
            'high_priority': high_priority,
            'overdue': overdue,
            'completion_rate': completion_rate,
        },
        'status_chart': {
            'labels': list(status_counts.keys()),
            'data': list(status_counts.values()),
        },
        'priority_chart': {
            'labels': list(priority_counts.keys()),
            'data': list(priority_counts.values()),
        },
        'monthly_chart': {
            'labels': months,
            'data': month_counts,
        },
        'recent_activity': recent_activity,
        'upcoming_deadlines': upcoming,
    }


@login_required
def dashboard_home(request):
    data = _build_dashboard_data(request.user)
    context = {
        'counters': data['counters'],
        'status_chart_json': data['status_chart'],
        'priority_chart_json': data['priority_chart'],
        'monthly_chart_json': data['monthly_chart'],
        'recent_activity': request.user.activity_logs.all()[:8],
        'upcoming_deadlines': Task.objects.filter(
            user=request.user
        ).exclude(status=Task.Status.COMPLETED).filter(
            deadline__isnull=False
        ).order_by('deadline')[:5],
        'has_tasks': Task.objects.filter(user=request.user).exists(),
    }
    return render(request, 'dashboard/home.html', context)


@login_required
def dashboard_data_api(request):
    """
    JSON endpoint polled/fetched via AJAX so the dashboard can refresh
    its counters and charts without a full page reload — e.g. right
    after a task is created or completed elsewhere in the app.
    """
    data = _build_dashboard_data(request.user)
    return JsonResponse(data)
