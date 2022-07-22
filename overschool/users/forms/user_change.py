from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from users.models import User


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ("email", "password")
