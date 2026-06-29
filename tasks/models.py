"""
Tasks app: the heart of the application. Defines Category and Task,
both scoped per-user so that one person's tasks/categories are never
visible to another (enforced again at the queryset level in views.py
— the model alone doesn't guarantee isolation, the view layer does).
"""
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from core.models import TimeStampedModel


class Category(TimeStampedModel):
    """
    A user-defined label for grouping tasks (e.g. "Work", "Personal",
    "Health"). Each user manages their own set of categories.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='categories',
    )
    name = models.CharField(max_length=80)
    color = models.CharField(
        max_length=7,
        default='#6C5DD3',
        help_text='Hex color used as a tag/badge accent, e.g. #6C5DD3',
    )

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['user', 'name'], name='unique_category_per_user'),
        ]

    def __str__(self):
        return self.name


class Task(TimeStampedModel):

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tasks',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
    )
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    deadline = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'priority']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('tasks:detail', kwargs={'pk': self.pk})

    @property
    def is_overdue(self):
        if self.deadline and self.status != self.Status.COMPLETED:
            return self.deadline < timezone.now()
        return False

    @property
    def priority_color(self):
        return {
            self.Priority.LOW: 'success',
            self.Priority.MEDIUM: 'warning',
            self.Priority.HIGH: 'danger',
        }.get(self.priority, 'secondary')

    @property
    def status_color(self):
        return {
            self.Status.PENDING: 'secondary',
            self.Status.IN_PROGRESS: 'info',
            self.Status.COMPLETED: 'success',
        }.get(self.status, 'secondary')

    def mark_completed(self):
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])

    def save(self, *args, **kwargs):
        # Keep completed_at consistent no matter how status changes
        # (via the detail form, the AJAX quick-toggle, or the admin).
        if self.status == self.Status.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != self.Status.COMPLETED:
            self.completed_at = None
        super().save(*args, **kwargs)
