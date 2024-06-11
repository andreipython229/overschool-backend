from rest_framework import serializers
from .models import TgUsers, Notifications


class TgUsersSerializer(serializers.ModelSerializer):

    class Meta:
        model = TgUsers
        fields = ('tg_user_id', 'first_name')


class NotificationsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notifications
        fields = '__all__'


# class MeetingsRemindersSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = MeetingsRemindersTG
#         fields = '__all__'


class SendMessageSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=5000)
    students_groups = serializers.ListField(
        child=serializers.IntegerField()
    )
