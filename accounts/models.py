"""
Accounts app: extends Django's built-in User model with a one-to-one
Profile model (avatar, bio, phone) rather than swapping out the User
model entirely. This is the recommended, least-risky way to add
custom fields to authentication in Django — it keeps django.contrib.auth
fully intact (admin, permissions, password reset, etc.) while still
giving us room to grow.
"""
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import TimeStampedModel


def avatar_upload_path(instance, filename):
    """Store avatars under media/avatars/<user_id>/<filename> so each
    user's uploads are namespaced and never collide."""
    ext = filename.split('.')[-1]
    return f'avatars/{instance.user_id}/avatar.{ext}'


class Profile(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    avatar = models.ImageField(
        upload_to=avatar_upload_path,
        blank=True,
        null=True,
        help_text='Profile picture, square images look best.',
    )
    bio = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    job_title = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return f"{self.user.username}'s profile"

    @property
    def avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return None

    @property
    def initials(self):
        """Used as a fallback avatar when no image has been uploaded —
        e.g. 'JD' for John Doe — rendered inside a colored circle."""
        name = self.user.get_full_name() or self.user.username
        parts = [p for p in name.split() if p]
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return name[:2].upper()


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Whenever a User is created, automatically create a matching
    Profile. This means the rest of the codebase can always assume
    `request.user.profile` exists, with no defensive checks needed.
    """
    if created:
        Profile.objects.create(user=instance)
    else:
        Profile.objects.get_or_create(user=instance)
