"""
Automated tests for the dashboard app: aggregate statistics.

Run with:  python manage.py test
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from tasks.models import Task

User = get_user_model()


class DashboardStatisticsTests(TestCase):
    """Test 6: dashboard statistics are computed correctly and are
    scoped to the logged-in user only."""

    def setUp(self):
        self.user = User.objects.create_user(username='dash', password='StrongPass123')
        self.other_user = User.objects.create_user(username='other', password='StrongPass123')
        self.client.login(username='dash', password='StrongPass123')

        Task.objects.create(user=self.user, title='T1', status=Task.Status.COMPLETED, priority=Task.Priority.HIGH)
        Task.objects.create(user=self.user, title='T2', status=Task.Status.PENDING, priority=Task.Priority.LOW)
        Task.objects.create(user=self.user, title='T3', status=Task.Status.IN_PROGRESS, priority=Task.Priority.HIGH)
        # Belongs to a different user — must never affect the counters above.
        Task.objects.create(user=self.other_user, title='Not counted', status=Task.Status.COMPLETED)

    def test_dashboard_page_loads_with_correct_counters(self):
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 200)
        counters = response.context['counters']
        self.assertEqual(counters['total'], 3)
        self.assertEqual(counters['completed'], 1)
        self.assertEqual(counters['pending'], 1)
        self.assertEqual(counters['in_progress'], 1)
        # High priority counts only non-completed high-priority tasks (T3).
        self.assertEqual(counters['high_priority'], 1)

    def test_dashboard_api_endpoint_returns_matching_json(self):
        response = self.client.get(reverse('dashboard:data_api'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['counters']['total'], 3)
        self.assertEqual(sum(data['status_chart']['data']), 3)
        self.assertEqual(sum(data['priority_chart']['data']), 3)

    def test_completion_rate_calculation(self):
        response = self.client.get(reverse('dashboard:data_api'))
        data = response.json()
        # 1 completed out of 3 tasks => 33.3%
        self.assertAlmostEqual(data['counters']['completion_rate'], 33.3, delta=0.1)
