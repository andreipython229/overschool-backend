from django.contrib.auth.models import Group
from rest_framework import serializers


class AccessDistributionSerializer(serializers.Serializer):
    pass
    # all_groups = list(Group.objects.all().values("name"))
    # # ROLES = [(group['name'], group['name']) for group in all_groups]
    # ROLES = [group["name"] for group in all_groups]
    #
    # user_id = serializers.IntegerField(required=True)
    # role = serializers.ChoiceField(required=True, choices=ROLES)
    # student_groups = serializers.ListField(
    #     child=serializers.IntegerField(), required=False
    # )
