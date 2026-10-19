from django.conf import settings
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from rest_framework_simplejwt.token_blacklist.models import(
    BlacklistedToken,
    OutstandingToken
)

@receiver(
    pre_delete,
    sender=settings.AUTH_USER_MODEL,
    dispatch_uid="accounts.blacklist_tokens_before_user_delete",
)
def blacklist_tokens_before_user_delete(
    sender,
    instance,
    using,
    **kwargs,
):
    tokens = OutstandingToken.objects.using(using).filter(
        user_id= instance.pk,
    )

    for token in tokens.iterator():
        BlacklistedToken.objects.using(using).get_or_create(
            token_id= token.pk,
        )