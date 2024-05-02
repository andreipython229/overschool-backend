from rest_framework import serializers
from .models import TgUsers, Notifications


class TgUsersSerializer(serializers.ModelSerializer):

    class Meta:
        model = TgUsers
        fields = ('tg_user_id', 'first_name')


# class NotificationsSerializer(serializers.ModelSerializer):
#
#     class Meta:
#         model = Notifications
#         fields = ('__all__')
