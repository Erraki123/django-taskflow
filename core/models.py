"""
Core app: holds cross-cutting concerns shared by every other app —
abstract base models, the activity-log model, context processors and
the request-logging middleware. Nothing here is tied to "tasks" or
"accounts" specifically, which is what makes it reusable.
"""
from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base model that adds self-updating created/updated
    timestamps to any model that inherits from it.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ActivityLog(TimeStampedModel):
    """
    A lightweight audit trail. Every meaningful action a user takes
    (creating a task, completing it, logging in, updating a profile...)
    can write a row here, which powers the "Recent activity" widget on
    the dashboard.
    """

    class ActionType(models.TextChoices):
        CREATED = 'created', 'Created'
        UPDATED = 'updated', 'Updated'
        DELETED = 'deleted', 'Deleted'
        COMPLETED = 'completed', 'Completed'
        STATUS_CHANGED = 'status_changed', 'Status changed'
        LOGGED_IN = 'logged_in', 'Logged in'
        LOGGED_OUT = 'logged_out', 'Logged out'
        REGISTERED = 'registered', 'Registered'
        PROFILE_UPDATED = 'profile_updated', 'Profile updated'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activity_logs',
    )
    action = models.CharField(max_length=20, choices=ActionType.choices)
    description = models.CharField(max_length=255)
    icon = models.CharField(
        max_length=40,
        default='fa-circle-info',
        help_text='Font Awesome icon class suffix, e.g. "fa-circle-check".',
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.created_at:%Y-%m-%d %H:%M}"

    @classmethod
    def log(cls, user, action, description, icon='fa-circle-info'):
        """Convenience helper so views can write a one-liner instead of
        constructing an ActivityLog instance by hand everywhere."""
        return cls.objects.create(user=user, action=action, description=description, icon=icon)
