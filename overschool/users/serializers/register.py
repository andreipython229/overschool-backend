from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
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


class LoginSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=256, required=True,
                                                error_messages={"required": "No password"},
                                                help_text="Пароль пользователя")
    email = serializers.EmailField(required=True,
                                              error_messages={"required": "No email"},
                                              help_text="Почта пользователя")

