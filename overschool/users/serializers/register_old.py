# СТАРАЯ РЕГИСТРАЦИЯ С РАССЫЛКОЙ ИНВАЙТОВ ПУСКАЙ БУДЕТ
# ЕСЛИ В БУДУЩЕМ БУДЕМ РЕАЛИЗОВЫВАТЬ ФУНКЦИОНАЛ

# from dj_rest_auth.registration.serializers import \
#     RegisterSerializer as _RegisterSerializer
# from dj_rest_auth.serializers import LoginSerializer as _LoginSerializer
# from dj_rest_auth.serializers import \
#     UserDetailsSerializer as _UserDetailsSerializer
# from django.contrib.auth.hashers import make_password
# from phonenumber_field.serializerfields import PhoneNumberField
# from rest_framework import serializers
# from rest_framework.exceptions import ValidationError
#
# from users.models import Profile, User, UserRole
#
#
# class RegisterSerializer(_RegisterSerializer):
#     username = serializers.CharField(max_length=255)
#     email = serializers.EmailField(max_length=255, allow_blank=True, required=False)
#     phone_number = PhoneNumberField(allow_blank=True, required=False)
#     group_name = serializers.CharField(max_length=255)
#
#     def get_cleaned_data(self):
#         data_dict = super().get_cleaned_data()
#         data_dict["group_name"] = self.validated_data.get("group_name", "")
#         data_dict["email"] = self.validated_data.get("email", "")
#         data_dict["phone_number"] = self.validated_data.get("phone_number", "")
#         if not data_dict["email"] and not data_dict["phone_number"]:
#             raise ValidationError("Укажи email либо номер телефона")
#         else:
#             return data_dict
#
#     def save(self, request):
#         cleaned_data = self.get_cleaned_data()
#         group_id = UserRole.objects.filter(name=cleaned_data["group_name"]).first().pk
#         user = User.objects.create(
#             username=cleaned_data["username"],
#             password=make_password(cleaned_data["password1"]),
#             email=cleaned_data["email"],
#             phone_number=cleaned_data["phone_number"],
#         )
#         user.groups.add(group_id)
#         return user
#
#
# UserModel = User
#
#
# class LoginSerializer(_LoginSerializer):
#     """Сериализатор входа в свою учетную запись."""
#
#     username = serializers.CharField(max_length=255, required=False, allow_blank=True)
#     email = serializers.CharField(max_length=255, required=False, allow_blank=True)
#     phone_number = PhoneNumberField(required=False, allow_blank=True)
#     password = serializers.CharField(style={"input_type": "password"})
#
#     def _validate_phone_number(self, phone_number, password):
#         if phone_number and password:
#             user = self.authenticate(phone_number=phone_number, password=password)
#             return user
#
#     def get_auth_user_using_orm(self, username, email, phone_number, password):
#         if email:
#             try:
#                 username = UserModel.objects.get(email__iexact=email).get_username()
#             except UserModel.DoesNotExist:
#                 pass
#         if phone_number:
#             try:
#                 username = UserModel.objects.get(phone_number__iexact=phone_number).get_username()
#             except UserModel.DoesNotExist:
#                 pass
#         if username:
#             return self._validate_username_email(username, '', password)
#         return None
#
#     def get_auth_user_using_allauth(self, username, email, phone_number, password):
#         if phone_number and password:
#             return self._validate_phone_number(phone_number, password)
#
#         # Authentication through email
#         if email and password:
#             return self._validate_email(email, password)
#
#         # Authentication through username
#         if username and password:
#             return self._validate_username(username, password)
#
#         # Authentication through either username or email
#         return self._validate_username_email(username, email, password)
#
#     def get_auth_user(self, username, email, phone_number, password):
#         return self.get_auth_user_using_orm(username, email, phone_number, password)
#
#     def validate(self, attrs):
#         username = attrs.get("username")
#         email = attrs.get("email")
#         password = attrs.get("password")
#         phone_number = attrs.get("phone_number")
#
#         user = self.get_auth_user(username, email, phone_number, password)
#
#         if not user:
#             raise ValidationError("Невозможно войти с предоставленными учетными данными")
#
#         self.validate_auth_user_status(user)
#
#         attrs["user"] = user
#         return attrs
#
#
# class UserDetailsSerializer(_UserDetailsSerializer):
#     class Meta:
#         extra_fields = []
#         if hasattr(UserModel, "USERNAME_FIELD"):
#             extra_fields.append(UserModel.USERNAME_FIELD)
#         if hasattr(UserModel, "EMAIL_FIELD"):
#             extra_fields.append(UserModel.EMAIL_FIELD)
#         if hasattr(UserModel, "phone_number"):
#             extra_fields.append("phone_number")
#         if hasattr(UserModel, "groups"):
#             extra_fields.append("groups")
#         model = UserModel
#         fields = ('pk', *extra_fields)
#         read_only_fields = ('email',)
#
#
# class InviteSerializer(serializers.Serializer):
#     sender_type = serializers.CharField(
#         max_length=10,
#         required=True,
#         error_messages={"required": "No sender type sent"},
#         help_text="Тип отправки сообщения с урлом и токеном может быть либо email либо phone",
#     )
#     recipient = serializers.CharField(
#         max_length=256,
#         required=True,
#         error_messages={"required": "No recipient sent"},
#         help_text="Телефон или почта того, кого регистрируют",
#     )
#     user_type = serializers.IntegerField(
#         required=True,
#         error_messages={"required": "No user type sent"},
#         help_text="Айди роли пользователя",
#     )
#     course_id = serializers.ListField(
#         child=serializers.IntegerField(),
#         required=False,
#         error_messages={"required": "No course id sent"},
#         help_text="Айди курса, на которого регистрируют пользователя",
#     )
#     group_id = serializers.ListField(
#         child=serializers.IntegerField(),
#         required=False,
#         error_messages={"required": "No group id sent"},
#         help_text="Айди группы, на которого регистрируют пользователя",
#     )
#
#     def validate(self, attrs):
#         if attrs.get("user_type") == 1 and not attrs.get("course_id") \
#                 or attrs.get("user_type") == 2 and not attrs.get("course_id") \
#                 or attrs.get("user_type") == 3 and not attrs.get("course_id") \
#                 or attrs.get("user_type") == 4 and not attrs.get("course_id"):
#             raise serializers.ValidationError("Для этой роли пользователя необходим id курса")
#         if attrs.get("user_type") == 1 and not attrs.get("group_id") \
#                 or attrs.get("user_type") == 2 and not attrs.get("group_id") \
#                 or attrs.get("user_type") == 3 and not attrs.get("group_id") \
#                 or attrs.get("user_type") == 4 and not attrs.get("group_id"):
#             raise serializers.ValidationError("Для этой роли пользователя необходим id группы")
#         return attrs
#
#
# class ValidTokenSerializer(serializers.Serializer):
#     token = serializers.CharField(max_length=256, required=True,
#                                   error_messages={"required": "No token"},
#                                   help_text="Токен, полученный при регистрации пользователя админом")
#
#
# class PasswordSerializer(serializers.Serializer):
#     password1 = serializers.CharField(max_length=256, required=True,
#                                       error_messages={"required": "Пароль слишком лёгкий"},
#                                       help_text="Пароль")
#     password2 = serializers.CharField(max_length=256, required=True,
#                                       error_messages={"required": "Пароли не совпали"},
#                                       help_text="Подтверждение пароля")
#
#     def validate(self, attrs):
#         if attrs.get("password1") != attrs.get("password2"):
#             raise ValidationError("Пароли не совпали")
#         return attrs
