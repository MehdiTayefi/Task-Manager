from rest_framework import serializers

from ..models import Task

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields= (
            "id",
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "owner",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "owner",
            "created_at",
            "updated_at",
        )