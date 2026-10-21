import json

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from rest_framework.exceptions import APIException
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from demo.api.serializers import DemoTokenRefreshSerializer


class BrowserTokenObtainPairSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].trim_whitespace = False


COOKIE_NAME = "taskly_refresh"
COOKIE_PATH = "/browser-auth/"


def set_refresh_cookie(response, value, max_age=None):
    response.set_cookie(
        COOKIE_NAME,
        value,
        max_age=int(api_settings.REFRESH_TOKEN_LIFETIME.total_seconds()) if max_age is None else max_age,
        httponly=True,
        secure=getattr(settings, "FRONTEND_AUTH_COOKIE_SECURE", not settings.DEBUG),
        samesite="Strict",
        path=COOKIE_PATH,
    )


def clear_refresh_cookie(response):
    response.delete_cookie(COOKIE_NAME, path=COOKIE_PATH, samesite="Strict")


@never_cache
@require_POST
@csrf_protect
def browser_login(request):
    if request.content_type != "application/json":
        return JsonResponse({"detail": "Send a JSON request body."}, status=415)
    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({"detail": "Expected a JSON object."}, status=400)

    serializer = BrowserTokenObtainPairSerializer(data=data, context={"request": request})
    try:
        serializer.is_valid(raise_exception=True)
    except APIException as exc:
        return JsonResponse({"errors": exc.detail}, status=exc.status_code)

    tokens = serializer.validated_data
    response = JsonResponse({"access": tokens["access"]})
    set_refresh_cookie(response, tokens["refresh"])
    return response


@never_cache
@require_POST
@csrf_protect
def browser_refresh(request):
    value = request.COOKIES.get(COOKIE_NAME)
    if not value:
        return JsonResponse({"detail": "Please sign in."}, status=401)

    serializer = DemoTokenRefreshSerializer(
        data={"refresh": value}, context={"request": request},
    )
    try:
        serializer.is_valid(raise_exception=True)
    except (APIException, TokenError):
        response = JsonResponse({"detail": "Your session has expired. Please sign in."}, status=401)
        clear_refresh_cookie(response)
        return response

    tokens = serializer.validated_data
    response = JsonResponse({"access": tokens["access"]})
    new_refresh = tokens.get("refresh", value)
    from django.utils import timezone
    expires = RefreshToken(new_refresh)["exp"]
    set_refresh_cookie(response, new_refresh, max_age=max(1, expires-int(timezone.now().timestamp())))
    return response


@never_cache
@require_POST
@csrf_protect
def browser_logout(request):
    value = request.COOKIES.get(COOKIE_NAME)
    if value:
        try:
            token = RefreshToken(value)
            from demo.api.services import delete_demo_user
            if not delete_demo_user(token.get(api_settings.USER_ID_CLAIM)):
                token.blacklist()
        except TokenError:
            pass
    response = HttpResponse(status=204)
    clear_refresh_cookie(response)
    return response
