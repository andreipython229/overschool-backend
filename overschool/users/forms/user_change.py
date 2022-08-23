from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from phonenumber_field.widgets import PhoneNumberPrefixWidget
from users.models import User


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ("email", "phone_number", "password")
        widgets = {
            "phone_number": PhoneNumberPrefixWidget(),
        }
