from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

User= get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )
    password_confirm= serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    class Meta:
        model= User
        fields= (
            "id",
            "username",
            "email",
            "password",
            "password_confirm",
        )
        read_only_fields= ("id", )

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({
                "password_confirm": "pass do not match"
            })

        candidate = User(
            username= attrs["username"],
            email= attrs["email"]
        )

        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({
                "password": exc.messages,
            })from exc

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        return User.objects.create_user(**validated_data)


class ActiveUserRefreshTokenSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        try:
            refresh= RefreshToken(attrs["refresh"])
        except TokenError as exc:
            raise InvalidToken(str(exc)) from exc

        user_id = refresh.get(api_settings.USER_ID_CLAIM)

        if user_id is None:
            raise InvalidToken("invalid refresh token.")

        user_exists = User.objects.filter(
            **{api_settings.USER_ID_FIELD: user_id},
            is_active= True,
        ).exists()

        if not user_exists:
            raise InvalidToken("user is unavailable.")

        return super().validate(attrs)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model= User
        fields= ("id", "username", "email")
        read_only_fields= fields

class DeleteAccountSerializer(serializers.Serializer):
    password= serializers.CharField(
        write_only= True,
        trim_whitespace= True,
        style= {"input_type": "password"},
    )

    def validate_password(self, value):
        user = self.context["request"].user

        if not user.check_password(value):
            raise serializers.ValidationError(
                "Current password is incorrect!"
            )

        return value