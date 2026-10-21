from django.db import transaction

from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.generics import RetrieveDestroyAPIView

from .serializers import (
    RegisterSerializer,
    ActiveUserRefreshTokenSerializer,
    UserSerializer,
    DeleteAccountSerializer
)
from demo.api.serializers import DemoTokenRefreshSerializer


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
    serializer_class= DemoTokenRefreshSerializer


class LogoutView(TokenBlacklistView):
    authentication_classes= []
    permission_classes= [AllowAny]

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(RetrieveDestroyAPIView):
    serializer_class= UserSerializer
    permission_classes= [IsAuthenticated]

    def get_object(self):
        user= self.request.user
        self.check_object_permissions(self.request, user)
        return user

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()

        serializer= DeleteAccountSerializer(
            data= request.data,
            context= self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            user.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)