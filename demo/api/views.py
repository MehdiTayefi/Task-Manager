import math

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from frontend.auth_views import COOKIE_NAME, set_refresh_cookie
from ..models import DemoSession
from .services import cleanup_expired, create_demo, delete_demo_user


class DemoCreateThrottle(SimpleRateThrottle):
    scope = "demo_create"

    def get_rate(self):
        return getattr(settings, "DEMO_CREATE_RATE", "10/hour")

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


@never_cache
@require_POST
@csrf_protect
def start_demo(request):
    throttle = DemoCreateThrottle()
    if not throttle.allow_request(request, None):
        response = JsonResponse({
            "detail": "تعداد درخواست‌های دمو زیاد است. کمی بعد دوباره امتحان کن."},
            status=429
        )
        response["Retry-After"] = str(max(1, math.ceil(throttle.wait() or 60)))
        return response
    
    cleanup_expired()

    previous = request.COOKIES.get(COOKIE_NAME)
    if previous:
        try:
            token = RefreshToken(previous)
            delete_demo_user(token.get(api_settings.USER_ID_CLAIM))
        except TokenError:
            pass
    session, tokens = create_demo()
    response = JsonResponse({
        "access": tokens["access"],
        "expires_at": session.expires_at.isoformat()
        },status=201
    )
    set_refresh_cookie(
        response,
        tokens["refresh"],
        max_age=max(1, int((session.expires_at-timezone.now()).total_seconds()))
    )
    return response


class DemoStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        session = DemoSession.objects.filter(user=request.user).first()
        response = Response({
            "is_demo": bool(session),
            "expires_at": session.expires_at.isoformat() if session else None}
        )
        response["Cache-Control"] = "no-store"
        return response
