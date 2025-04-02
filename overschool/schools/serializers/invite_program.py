from rest_framework import serializers
from schools.models import InviteProgram


class InviteProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = InviteProgram
        fields = "__all__"
        read_only_fields = ["school"]
