from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import Profile

User = get_user_model()


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0
    fields = ('avatar', 'job_title', 'bio', 'phone_number')


class CustomUserAdmin(UserAdmin):
    """Extends the default UserAdmin so the Profile fields are
    editable right inside the User edit page, and adds a column
    showing how many tasks each user owns — handy for support."""
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined', 'task_count')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')

    @admin.display(description='Tasks')
    def task_count(self, obj):
        return obj.tasks.count()


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.site_header = 'TaskFlow Administration'
admin.site.site_title = 'TaskFlow Admin'
admin.site.index_title = 'Welcome to the TaskFlow control panel'
