"""
Management command to populate the database with a demo user and a
realistic set of tasks/categories, so a freshly-cloned project shows
a populated, convincing dashboard immediately instead of an empty
shell.

Usage:
    python manage.py seed_demo_data
"""
import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import ActivityLog
from tasks.models import Category, Task

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates a demo user (demo / Demo@12345) with sample categories and tasks.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username', default='demo',
            help='Username for the demo account (default: demo)',
        )

    def handle(self, *args, **options):
        username = options['username']
        password = 'Demo@12345'

        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': f'{username}@example.com', 'first_name': 'Demo', 'last_name': 'User'},
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created demo user "{username}" / password "{password}"'))
        else:
            self.stdout.write(self.style.WARNING(f'User "{username}" already exists — reusing it.'))

        category_specs = [
            ('Work', '#6C5DD3'),
            ('Personal', '#2ED9A3'),
            ('Health', '#FF6B6B'),
            ('Learning', '#4FB6F0'),
        ]
        categories = []
        for name, color in category_specs:
            cat, _ = Category.objects.get_or_create(user=user, name=name, defaults={'color': color})
            categories.append(cat)

        task_titles = [
            'Prepare quarterly investor deck',
            'Review pull request #482',
            'Book dentist appointment',
            'Plan team offsite',
            'Write project retrospective',
            'Renew gym membership',
            'Read "Atomic Habits" — chapter 4',
            'Refactor authentication module',
            'Grocery shopping for the week',
            'Update résumé',
            'Schedule 1:1 with manager',
            'Fix mobile responsive layout bug',
            'Pay electricity bill',
            'Prepare slides for client demo',
            'Research competitor pricing',
            'Morning run — 5km',
            'Backup production database',
            'Submit expense report',
        ]

        statuses = [Task.Status.PENDING, Task.Status.IN_PROGRESS, Task.Status.COMPLETED]
        priorities = [Task.Priority.LOW, Task.Priority.MEDIUM, Task.Priority.HIGH]

        created_count = 0
        now = timezone.now()
        for i, title in enumerate(task_titles):
            if Task.objects.filter(user=user, title=title).exists():
                continue
            status = random.choices(statuses, weights=[3, 2, 4])[0]
            deadline = now + timedelta(days=random.randint(-5, 14)) if random.random() > 0.25 else None
            created_at_offset = random.randint(0, 150)

            task = Task.objects.create(
                user=user,
                title=title,
                description=f'Auto-generated demo task #{i + 1} for showcasing the dashboard.',
                category=random.choice(categories),
                priority=random.choice(priorities),
                status=status,
                deadline=deadline,
            )
            # Backdate created_at so the "tasks per month" chart has spread.
            task.created_at = now - timedelta(days=created_at_offset)
            task.save(update_fields=['created_at'])
            created_count += 1

        ActivityLog.log(user, ActivityLog.ActionType.CREATED, 'Seeded demo data', icon='fa-database')

        self.stdout.write(self.style.SUCCESS(
            f'Done. Created {created_count} new demo tasks across {len(categories)} categories for "{username}".'
        ))
