from django.contrib.auth.models import Group
from django.utils import timezone
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


class SignupSchoolOwnerSerializer(serializers.Serializer):
    school_name = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)
    phone_number = PhoneNumberField(required=True)
    password = serializers.CharField(write_only=True)
    password_confirmation = serializers.CharField(write_only=True)

    def validate(self, attrs):
        referral_code = self.context.get("referral_code")
        if referral_code:
            attrs["referral_code"] = referral_code
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

        attrs["school_name"] = translit(attrs.get("school_name"), "ru", reversed=True)
        return attrs

    def create(self, validated_data):
        school_name = validated_data.pop("school_name")
        referral_code = validated_data.pop("referral_code", None)

        email = validated_data.get("email")
        password = validated_data.pop("password")
        validated_data.pop("password_confirmation", None)

        user = User.objects.filter(email__iexact=email).first()

        if not user:
            # Если пользователя нет — создаём его
            user = User(**validated_data)
            user.set_password(password)
            user.save()

        trial_days = 14

        if referral_code:
            trial_days += 21

        school = School(
            name=school_name,
            owner=user,
            tariff=Tariff.objects.get(name=TariffPlan.JUNIOR.value),
            used_trial=True,
            trial_end_date=timezone.now() + timezone.timedelta(days=trial_days),
        )

        school.save()

        # Создаем запись реферрала, если указан реферральный код
        if referral_code:
            referrer_school = School.objects.get(referral_code=referral_code)
            Referral.objects.create(
                referrer_school=referrer_school, referred_school=school
            )

        if school:
            school_header = SchoolHeader(school=school, name=school.name)
            school_header.save()
            SchoolDocuments.objects.create(school=school, user=user)

        group = Group.objects.get(name="Admin")
        user.groups.create(group=group, school=school)
        return user

    def update(self, instance, validated_data):
        instance.email = validated_data.get("email", instance.email)
        instance.phone_number = validated_data.get(
            "phone_number", instance.phone_number
        )
        instance.save()
        return instance
