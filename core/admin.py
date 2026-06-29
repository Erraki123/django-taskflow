from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'description', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'description')
    date_hierarchy = 'created_at'
    readonly_fields = ('user', 'action', 'description', 'icon', 'created_at', 'updated_at')

    def has_add_permission(self, request):
        # Activity logs are created programmatically, not by hand.
        return False
