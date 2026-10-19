from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from ..models import Task
from ..pagination import TaskPagination
from ..permissions import IsTaskOwner
from .serialziers import TaskSerializer

class TaskViewSet(ModelViewSet):
    serializer_class= TaskSerializer
    permission_classes= [IsAuthenticated, IsTaskOwner]
    pagination_class= TaskPagination

    filter_backends= [DjangoFilterBackend]
    filterset_fields= ("status", "priority")

    http_method_names= [
        "get",
        "post",
        "patch",
        "delete",
        "head",
        "options",
    ]

    def get_queryset(self):
        return Task.objects.filter(
            owner= self.request.user,
        ).order_by("-created_at", "-id")

    def perform_create(self, serializer):
        return serializer.save(owner=self.request.user)