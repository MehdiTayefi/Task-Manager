from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Task

@admin.register(Task)
class TaskAdmin(ModelAdmin):
    list_display= (
        "id",
        "title",
        "owner",
        "description",
        "status",
        "priority",
        "due_date",
        "created_at",
    )

    list_filter= ("status", "priority")
    search_fields= ("title", "owner__username")
    autocomplete_fields= ("owner", )
    readonly_fields= ("created_at", "updated_at")
    list_select_related= ("owner", )

