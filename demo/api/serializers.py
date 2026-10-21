from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.api.serializers import ActiveUserRefreshTokenSerializer
from ..models import DemoSession
from .services import cap_tokens


class DemoTokenRefreshSerializer(ActiveUserRefreshTokenSerializer):
    def validate(self, attrs):
        try:
            token = RefreshToken(attrs["refresh"])
        except TokenError as exc:
            raise InvalidToken(str(exc)) from exc
        session = DemoSession.objects.filter(user_id=token.get(api_settings.USER_ID_CLAIM)).first()
        if session and session.expires_at <= timezone.now():
            get_user_model().objects.filter(pk=session.user_id).delete()
            raise InvalidToken("فضای آزمایشی منقضی شده است.")
        tokens = super().validate(attrs)
        return cap_tokens(tokens, session.expires_at) if session else tokens
