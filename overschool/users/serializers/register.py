from rest_framework import serializers
from users.models import User
from django.contrib.auth import authenticate


class RegistrationSerializer(serializers.ModelSerializer):
    """ Сериализация регистрации пользователя и создания нового. """

    password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True
    )
    token = serializers.CharField(max_length=255, read_only=True)
    group = serializers.IntegerField(help_text="Id группы")

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'group', 'token']

    def create(self, validated_data):
        print(validated_data.keys())
        print({x: validated_data[x] for x in validated_data if x != 'group'})
        return User.objects.create_user(**{x: validated_data[x] for x in validated_data if x != 'group'})

class RegisterAdminSerializer(serializers.Serializer):
    sender_type = serializers.CharField(max_length=10, required=True,
                                        error_messages={"required": "No sender type sent"},
                                        help_text="Тип отправки сообщения с урлом и токеном может быть либо mail либо phone")
    recipient = serializers.CharField(max_length=256, required=True,
                                      error_messages={"required": "No recipient sent"},
                                      help_text="Телефон или почта того, кого регистрируют")
    user_type = serializers.IntegerField(required=True,
                                         error_messages={"required": "No user type sent"},
                                         help_text="Айди роли пользователя")
    course_id = serializers.IntegerField(required=True,
                                         error_messages={"required": "No course id sent"},
                                         help_text="Айди курса, на которого регистрируют пользователя")


class FirstRegisterSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=256, required=True,
                                  error_messages={"required": "No token"},
                                  help_text="Токен, полученный при регистрации пользователя админом")


class LoginPrSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=256, required=True,
                                                error_messages={"required": "No password"},
                                                help_text="Пароль пользователя")
    email = serializers.EmailField(required=True,
                                              error_messages={"required": "No email"},
                                              help_text="Почта пользователя")

class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=255)
    username = serializers.CharField(max_length=255, read_only=True)
    password = serializers.CharField(max_length=128, write_only=True)
    token = serializers.CharField(max_length=255, read_only=True)

    def validate(self, data):
        email = data.get('email', None)
        password = data.get('password', None)

        if email is None:
            raise serializers.ValidationError(
                'An email address is required to log in.'
            )

        if password is None:
            raise serializers.ValidationError(
                'A password is required to log in.'
            )

        user = authenticate(username=email, password=password)


        if user is None:
            raise serializers.ValidationError(
                'A user with this email and password was not found.'
            )

        if not user.is_active:
            raise serializers.ValidationError(
                'This user has been deactivated.'
            )

        return {
            'email': user.email,
            'username': user.username,
            'token': user.token
        }

