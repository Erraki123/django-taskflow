"""
Tasks app views.

Every queryset here is filtered by `user=request.user` (or
`task.user_id == request.user.id` for object-level checks) so that
one account can never read, edit, or delete another account's data.
That filtering is the actual security boundary — @login_required only
keeps anonymous users out, it says nothing about *whose* tasks a
logged-in user can touch.
"""
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods, require_POST

from core.models import ActivityLog

from .forms import CategoryForm, TaskForm
from .models import Category, Task


def _user_tasks(user):
    """Single source of truth for 'this user's tasks' so every view
    (and the dashboard app) filters identically."""
    return Task.objects.filter(user=user).select_related('category')


@login_required
def task_list(request):
    tasks = _user_tasks(request.user)

    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    category_filter = request.GET.get('category', '')
    sort = request.GET.get('sort', '-created_at')

    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    if category_filter:
        tasks = tasks.filter(category_id=category_filter)

    allowed_sorts = {
        '-created_at', 'created_at',
        '-deadline', 'deadline',
        '-priority', 'priority',
        'title', '-title',
    }
    if sort not in allowed_sorts:
        sort = '-created_at'
    tasks = tasks.order_by(sort)

    paginator = Paginator(tasks, settings.TASKS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'tasks': page_obj.object_list,
        'categories': Category.objects.filter(user=request.user),
        'search_query': search_query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'category_filter': category_filter,
        'sort': sort,
        'status_choices': Task.Status.choices,
        'priority_choices': Task.Priority.choices,
        'total_count': tasks.count(),
    }

    # AJAX search/filter: return only the table/cards partial, not the
    # full page shell, so the request stays cheap and the page never
    # flickers.
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('tasks/partials/task_table.html', context, request=request)
        return JsonResponse({
            'html': html,
            'count': context['total_count'],
        })

    return render(request, 'tasks/task_list.html', context)


@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            ActivityLog.log(
                user=request.user,
                action=ActivityLog.ActionType.CREATED,
                description=f'Created task "{task.title}"',
                icon='fa-circle-plus',
            )
            messages.success(request, f'Task "{task.title}" was created successfully.')
            return redirect('tasks:list')
        messages.error(request, 'Please fix the errors below.')
    else:
        form = TaskForm(user=request.user)

    return render(request, 'tasks/task_form.html', {'form': form, 'is_edit': False})


@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            form.save()
            ActivityLog.log(
                user=request.user,
                action=ActivityLog.ActionType.UPDATED,
                description=f'Updated task "{task.title}"',
                icon='fa-pen',
            )
            messages.success(request, f'Task "{task.title}" was updated successfully.')
            return redirect('tasks:list')
        messages.error(request, 'Please fix the errors below.')
    else:
        form = TaskForm(instance=task, user=request.user)

    return render(request, 'tasks/task_form.html', {'form': form, 'is_edit': True, 'task': task})


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    return render(request, 'tasks/task_detail.html', {'task': task})


@login_required
@require_POST
def task_delete(request, pk):
    """
    AJAX-only delete. Returns JSON so the front-end can remove the row
    from the DOM with an animation instead of reloading the page.
    """
    task = get_object_or_404(Task, pk=pk, user=request.user)
    title = task.title
    task.delete()
    ActivityLog.log(
        user=request.user,
        action=ActivityLog.ActionType.DELETED,
        description=f'Deleted task "{title}"',
        icon='fa-trash',
    )
    return JsonResponse({'success': True, 'message': f'Task "{title}" was deleted.'})


@login_required
@require_POST
def task_update_status(request, pk):
    """AJAX endpoint to change just the status (e.g. from a dropdown
    or a quick "mark complete" button in the task list)."""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    new_status = request.POST.get('status')

    if new_status not in Task.Status.values:
        return JsonResponse({'success': False, 'message': 'Invalid status.'}, status=400)

    task.status = new_status
    task.save()

    ActivityLog.log(
        user=request.user,
        action=ActivityLog.ActionType.STATUS_CHANGED,
        description=f'Marked "{task.title}" as {task.get_status_display()}',
        icon='fa-circle-check' if new_status == Task.Status.COMPLETED else 'fa-arrows-rotate',
    )

    return JsonResponse({
        'success': True,
        'status': task.status,
        'status_display': task.get_status_display(),
        'status_color': task.status_color,
        'message': f'Task marked as {task.get_status_display()}.',
    })


@login_required
@require_POST
def task_update_priority(request, pk):
    """AJAX endpoint to change just the priority."""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    new_priority = request.POST.get('priority')

    if new_priority not in Task.Priority.values:
        return JsonResponse({'success': False, 'message': 'Invalid priority.'}, status=400)

    task.priority = new_priority
    task.save()

    ActivityLog.log(
        user=request.user,
        action=ActivityLog.ActionType.UPDATED,
        description=f'Set "{task.title}" priority to {task.get_priority_display()}',
        icon='fa-flag',
    )

    return JsonResponse({
        'success': True,
        'priority': task.priority,
        'priority_display': task.get_priority_display(),
        'priority_color': task.priority_color,
        'message': f'Priority updated to {task.get_priority_display()}.',
    })


# ----------------------------------------------------------------------
# Categories
# ----------------------------------------------------------------------

@login_required
def category_list(request):
    categories = Category.objects.filter(user=request.user).prefetch_related('tasks')
    return render(request, 'tasks/category_list.html', {'categories': categories})


@login_required
@require_http_methods(['GET', 'POST'])
def category_create(request):
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        form = CategoryForm(request.POST, user=request.user)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'id': category.id,
                    'name': category.name,
                    'color': category.color,
                })
            messages.success(request, f'Category "{category.name}" created.')
            return redirect('tasks:category_list')
        if is_ajax:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
        messages.error(request, 'Please fix the errors below.')
    else:
        form = CategoryForm(user=request.user)

    return render(request, 'tasks/category_form.html', {'form': form})


@login_required
@require_POST
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    name = category.name
    category.delete()
    messages.info(request, f'Category "{name}" was deleted. Its tasks remain, now uncategorized.')
    return redirect('tasks:category_list')
