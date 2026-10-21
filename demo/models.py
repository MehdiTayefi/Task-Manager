from django.conf import settings
from django.db import models


class DemoSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="demo_session",
    )
    created_at= models.DateTimeField(auto_now_add=True)
    expires_at= models.DateTimeField(db_index=True)

    class Meta:
        ordering= ("expires_at", )