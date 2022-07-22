from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    sender_type = serializers.CharField(max_length=10, required=True,
                                        error_messages={"required": "No sender type sent"})
    recipient = serializers.CharField(max_length=256, required=True,
                                      error_messages={"required": "No recipient sent"})
    user_type = serializers.IntegerField(required=True,
                                         error_messages={"required": "No user type sent"})