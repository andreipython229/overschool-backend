from django.contrib.auth.models import Group
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from schools.models import School, Tariff, TariffPlan
from users.models import User


class SignupSchoolOwnerSerializer(serializers.Serializer):
    school_name = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)
    phone_number = PhoneNumberField(required=True)
    password = serializers.CharField(write_only=True)
    password_confirmation = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if not attrs.get("email"):
            raise serializers.ValidationError("'email' is required.")
        if not attrs.get("phone_number"):
            raise serializers.ValidationError("'phone_number' is required.")
        if not attrs.get("school_name"):
            raise serializers.ValidationError("'school_name' is required.")
        password = attrs.get("password")
        password_confirmation = attrs.get("password_confirmation")
        if password and password != password_confirmation:
            raise serializers.ValidationError("Passwords do not match.")

        return attrs

    def create(self, validated_data):
        # Извлекаем school_name из validated_data
        school_name = validated_data.pop("school_name")

        # Создаем пользователя и связываем его с школой
        validated_data.pop("password_confirmation")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        school = School(
            name=school_name,
            owner=user,
            tariff=Tariff.objects.get(name=TariffPlan.INTERN.value),
        )

        school.save()
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
