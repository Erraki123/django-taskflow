"""
Automated tests for the tasks app.

Run with:  python manage.py test
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Task

User = get_user_model()


class TaskModelTests(TestCase):
    """Sanity checks on the Task model's own logic (not view-layer)."""

    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='StrongPass123')

    def test_completed_at_is_set_when_status_becomes_completed(self):
        task = Task.objects.create(user=self.user, title='Write report', status=Task.Status.PENDING)
        self.assertIsNone(task.completed_at)
        task.status = Task.Status.COMPLETED
        task.save()
        self.assertIsNotNone(task.completed_at)

    def test_is_overdue_true_for_past_deadline_when_not_completed(self):
        past = timezone.now() - timezone.timedelta(days=1)
        task = Task.objects.create(user=self.user, title='Late task', deadline=past, status=Task.Status.PENDING)
        self.assertTrue(task.is_overdue)

    def test_is_overdue_false_once_completed(self):
        past = timezone.now() - timezone.timedelta(days=1)
        task = Task.objects.create(user=self.user, title='Late but done', deadline=past, status=Task.Status.COMPLETED)
        self.assertFalse(task.is_overdue)


class TaskCRUDViewTests(TestCase):
    """
    Covers the required CRUD scenarios: create, update, delete — plus
    the permission boundary that one user can never touch another
    user's tasks.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='bob', password='StrongPass123')
        self.other_user = User.objects.create_user(username='carol', password='StrongPass123')
        self.client.login(username='bob', password='StrongPass123')
        self.category = Category.objects.create(user=self.user, name='Work', color='#6C5DD3')

    def test_task_creation(self):
        """Test 3: creating a task via the form persists it correctly."""
        response = self.client.post(reverse('tasks:create'), {
            'title': 'Prepare slides',
            'description': 'For Monday meeting',
            'category': self.category.id,
            'priority': Task.Priority.HIGH,
            'status': Task.Status.PENDING,
            'deadline': '',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Task.objects.filter(user=self.user, title='Prepare slides').exists())
        task = Task.objects.get(title='Prepare slides')
        self.assertEqual(task.priority, Task.Priority.HIGH)

    def test_task_update(self):
        """Test 4: editing an existing task changes its stored fields."""
        task = Task.objects.create(user=self.user, title='Old title', priority=Task.Priority.LOW)
        response = self.client.post(reverse('tasks:update', args=[task.id]), {
            'title': 'Updated title',
            'description': '',
            'category': '',
            'priority': Task.Priority.HIGH,
            'status': Task.Status.IN_PROGRESS,
            'deadline': '',
        })
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.title, 'Updated title')
        self.assertEqual(task.priority, Task.Priority.HIGH)
        self.assertEqual(task.status, Task.Status.IN_PROGRESS)

    def test_task_deletion(self):
        """Test 5: the AJAX delete endpoint removes the task and
        returns a success JSON payload."""
        task = Task.objects.create(user=self.user, title='Disposable task')
        response = self.client.post(reverse('tasks:delete', args=[task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': True, 'message': 'Task "Disposable task" was deleted.'})
        self.assertFalse(Task.objects.filter(id=task.id).exists())

    def test_user_cannot_access_another_users_task(self):
        """Security: task detail/update/delete must 404 for a task
        that belongs to a different user."""
        foreign_task = Task.objects.create(user=self.other_user, title='Not yours')

        detail_response = self.client.get(reverse('tasks:detail', args=[foreign_task.id]))
        self.assertEqual(detail_response.status_code, 404)

        delete_response = self.client.post(reverse('tasks:delete', args=[foreign_task.id]))
        self.assertEqual(delete_response.status_code, 404)
        self.assertTrue(Task.objects.filter(id=foreign_task.id).exists())

    def test_task_list_only_shows_own_tasks(self):
        Task.objects.create(user=self.user, title='Mine')
        Task.objects.create(user=self.other_user, title='Not mine')

        response = self.client.get(reverse('tasks:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mine')
        self.assertNotContains(response, 'Not mine')

    def test_ajax_status_update(self):
        task = Task.objects.create(user=self.user, title='Toggle me', status=Task.Status.PENDING)
        response = self.client.post(
            reverse('tasks:update_status', args=[task.id]),
            {'status': Task.Status.COMPLETED},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.COMPLETED)

    def test_search_filters_task_list(self):
        Task.objects.create(user=self.user, title='Buy groceries')
        Task.objects.create(user=self.user, title='File taxes')

        response = self.client.get(reverse('tasks:list'), {'q': 'groceries'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Buy groceries', response.json()['html'])
        self.assertNotIn('File taxes', response.json()['html'])
