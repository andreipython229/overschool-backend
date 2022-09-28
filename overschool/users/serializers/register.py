from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from rest_framework.exceptions import ValidationError
from users.models import User, Profile
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer
from phonenumber_field.serializerfields import PhoneNumberField


class RegistrationSerializer(RegisterSerializer):
    username = serializers.CharField(max_length=255)
    email = serializers.EmailField(max_length=255, allow_blank=True)
    phone_number = PhoneNumberField(allow_blank=True)

    def get_cleaned_data(self):
        data_dict = super().get_cleaned_data()
        data_dict['email'] = self.validated_data.get('email', '')
        data_dict['phone_number'] = self.validated_data.get('phone_number', '')
        if not data_dict['email'] and not data_dict['phone_number']:
            raise ValidationError("Укажи email либо номер телефона")
        else:
            return data_dict

    def save(self, request):
        cleaned_data = self.get_cleaned_data()

        user = User.objects.create(
            username=cleaned_data['username'],
            password=make_password(cleaned_data['password1']),
            email=cleaned_data['email'],
            phone_number=cleaned_data['phone_number'],
        )
        return user


UserModel = User


class LoginSerializer(LoginSerializer):
    """Сериализатор входа в свою учетную запись."""

    username = serializers.CharField(max_length=255, required=False, allow_blank=True)
    email = serializers.CharField(max_length=255, required=False, allow_blank=True)
    phone_number = PhoneNumberField(required=False, allow_blank=True)
    password = serializers.CharField(style={'input_type': 'password'})

    def _validate_phone_number(self, phone_number, password):
        if phone_number and password:
            user = self.authenticate(phone_number=phone_number, password=password)
            return user

    def get_auth_user_using_orm(self, username, email, phone_number, password):
        if email:
            try:
                username = UserModel.objects.get(email__iexact=email).get_username()
            except UserModel.DoesNotExist:
                pass
        if phone_number:
            try:
                username = UserModel.objects.get(phone_number__iexact=phone_number).get_username()
            except UserModel.DoesNotExist:
                pass
        if username:
            return self._validate_username_email(username, '', password)
        return None

    def get_auth_user_using_allauth(self, username, email, phone_number, password):
        if phone_number and password:
            return self._validate_phone_number(phone_number, password)

        # Authentication through email
        if email and password:
            return self._validate_email(email, password)

        # Authentication through username
        if username and password:
            return self._validate_username(email, password)

        # Authentication through either username or email
        return self._validate_username_email(username, email, password)

    def get_auth_user(self, username, email, phone_number, password):
        return self.get_auth_user_using_orm(username, email, phone_number, password)

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')
        phone_number = attrs.get('phone_number')

        user = self.get_auth_user(username, email, phone_number, password)

        if not user:
            print("Ошибка")

        self.validate_auth_user_status(user)

        attrs['user'] = user
        return attrs


class InviteSerializer(serializers.Serializer):
    sender_type = serializers.CharField(
        max_length=10,
        required=True,
        error_messages={"required": "No sender type sent"},
        help_text="Тип отправки сообщения с урлом и токеном может быть либо email либо phone",
    )
    recipient = serializers.CharField(
        max_length=256,
        required=True,
        error_messages={"required": "No recipient sent"},
        help_text="Телефон или почта того, кого регистрируют",
    )
    user_type = serializers.IntegerField(
        required=True,
        error_messages={"required": "No user type sent"},
        help_text="Айди роли пользователя",
    )
    course_id = serializers.IntegerField(
        required=False,
        error_messages={"required": "No course id sent"},
        help_text="Айди курса, на которого регистрируют пользователя",
    )

    # def validate(self, data):
    #     if not data['course_id']:
    #         raise serializers.ValidationError("Для этой роли пользователя необходим id курса")
    #     return data


class ValidTokenSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=256, required=True,
                                  error_messages={"required": "No token"},
                                  help_text="Токен, полученный при регистрации пользователя админом")
