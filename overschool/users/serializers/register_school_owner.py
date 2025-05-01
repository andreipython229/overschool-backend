import logging

from allauth.account.models import EmailAddress
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from schools.models import (
    Referral,
    School,
    SchoolDocuments,
    SchoolHeader,
    Tariff,
    TariffPlan,
)
from transliterate import translit
from users.models import User

logger = logging.getLogger(__name__)


class SignupSchoolOwnerSerializer(serializers.Serializer):
    school_name = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)
    phone_number = PhoneNumberField(required=True)
    password = serializers.CharField(write_only=True)
    password_confirmation = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if not attrs.get("email"):
            raise serializers.ValidationError("'email' обязателеное поле.")
        if not attrs.get("phone_number"):
            raise serializers.ValidationError("'phone_number' обязателеное поле.")
        if not attrs.get("school_name"):
            raise serializers.ValidationError("'school_name' обязателеное поле.")

        email = attrs["email"]
        password = attrs["password"]

        user = User.objects.filter(email__iexact=email).first()
        if user:
            # Если пользователь есть, проверяем его пароль
            if not user.check_password(password):
                raise serializers.ValidationError(
                    "Неверный пароль для указанного email."
                )
        else:
            # Если пользователь новый, проверяем совпадение паролей
            password_confirmation = attrs.get("password_confirmation")
            if not password_confirmation:
                raise serializers.ValidationError("Подтвердите пароль.")
            if password != password_confirmation:
                raise serializers.ValidationError("Пароли не совпадают.")

        attrs["school_name"] = translit(
            attrs.get("school_name"), "ru", reversed=True
        ).replace(" ", "_")
        return attrs

    def create(self, validated_data):
        email = validated_data.get("email")
        phone_number = validated_data.get("phone_number")
        password = validated_data.get("password")

        user = User.objects.filter(email__iexact=email).first()

        if user:
            pass
        else:
            logger.info(f"Creating new user with email {email}")

            create_data = {"email": email}

            user = User(**create_data)
            user.phone_number = phone_number
            user.set_password(password)
            try:
                user.save()
                try:
                    EmailAddress.objects.create(
                        user=user, email=user.email, primary=True, verified=True
                    )
                except ImportError:
                    logger.warning(
                        "allauth.account.models.EmailAddress not found, skipping EmailAddress creation."
                    )
                except Exception as ea_e:
                    logger.error(
                        f"Failed to create EmailAddress for {user.email}: {ea_e}",
                        exc_info=True,
                    )

            except Exception as e:
                logger.error(f"Error saving new user {email}: {e}", exc_info=True)
                raise serializers.ValidationError(
                    "Не удалось сохранить нового пользователя."
                )

        return user


class CreateSchoolSerializer(serializers.Serializer):
    school_name = serializers.CharField(required=True, max_length=255)
    phone_number = PhoneNumberField(required=True)

    def validate_school_name(self, value):

        name_translit = translit(value, "ru", reversed=True).replace(" ", "_")
        if School.objects.filter(name=name_translit).exists():
            raise serializers.ValidationError("Школа с таким названием уже существует.")
        return name_translit
