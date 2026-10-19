from django.db import models
from django.conf import settings


class Task(models.Model):
    class Status(models.TextChoices):
        TODO= "todo", "TO do"
        IN_PROGRESS= "in_progress", "IN progres"
        DONE= "done", "Done"

    class Priority(models.TextChoices):
        LOW= "low", "Low"
        MEDIUM= "medium", "Medium"
        HIGH= "high", "High"

    owner= models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks"
    )
    title= models.CharField(max_length=200)
    description= models.TextField(blank=True, default="")
    status= models.CharField(
        max_length=20,
        choices= Status.choices,
        default= Status.TODO,
    )
    priority= models.CharField(
        max_length=20,
        choices= Priority.choices,
        default= Priority.MEDIUM
    )
    due_date= models.DateField(blank=True, null=True)
    created_at= models.DateTimeField(auto_now_add=True)
    updated_at= models.DateTimeField(auto_now=True)

    class Meta:
        ordering= ["-created_at", "-id"]

    def __str__(self):
        return self.title