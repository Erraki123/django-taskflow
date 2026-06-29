from django.contrib import admin

from .models import Category, Task


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'color_preview', 'task_count', 'created_at')
    list_filter = ('user',)
    search_fields = ('name', 'user__username', 'user__email')

    @admin.display(description='Color')
    def color_preview(self, obj):
        from django.utils.html import format_html
        return format_html(
            '<span style="display:inline-block;width:16px;height:16px;border-radius:4px;'
            'background:{};border:1px solid #ddd;"></span> {}',
            obj.color, obj.color,
        )

    @admin.display(description='Tasks')
    def task_count(self, obj):
        return obj.tasks.count()


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'priority', 'status', 'deadline', 'is_overdue_display', 'created_at')
    list_filter = ('status', 'priority', 'category', 'created_at')
    search_fields = ('title', 'description', 'user__username', 'user__email')
    date_hierarchy = 'created_at'
    list_per_page = 25
    autocomplete_fields = []
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    fieldsets = (
        ('Task information', {
            'fields': ('user', 'title', 'description', 'category')
        }),
        ('Status & priority', {
            'fields': ('priority', 'status', 'deadline')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(boolean=True, description='Overdue')
    def is_overdue_display(self, obj):
        return obj.is_overdue
