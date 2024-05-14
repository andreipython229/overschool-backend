from rest_framework import serializers
from schools.models import SchoolMeetings


class SchoolMeetingsSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = SchoolMeetings