from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from .serializers import RegisterSerializer, ActiveUserRefreshTokenSerializer

class RegisterView(CreateAPIView):
    serializer_class= RegisterSerializer
    permission_classes= [AllowAny]
    authentication_classes= []

class LoginView(TokenObtainPairView):
    authentication_classes= []
    permission_classes= [AllowAny]

class RefreshView(TokenRefreshView):
    authentication_classes= []
    permission_classes= [AllowAny]
    serializer_class= ActiveUserRefreshTokenSerializer

class LogoutView(TokenBlacklistView):
    authentication_classes= []
    permission_classes= [AllowAny]

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT)