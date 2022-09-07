from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField, UsernameField
from phonenumber_field.formfields import PhoneNumberField
from users.models import User


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = "__all__"
        field_classes = {"username": UsernameField, "phone_number": PhoneNumberField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        password = self.fields.get("password")
        if password:
            password.help_text = password.help_text.format("../password/")
        user_permissions = self.fields.get("user_permissions")
        if user_permissions:
            user_permissions.queryset = user_permissions.queryset.select_related("content_type")
