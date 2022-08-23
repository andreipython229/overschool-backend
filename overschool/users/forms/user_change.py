from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from phonenumber_field.formfields import PhoneNumberField
from users.models import User


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()
    phone_number = PhoneNumberField()

    class Meta:
        model = User
        fields = ("email", "phone_number", "password")
