from .models import VideoModel
from rest_framework import serializers


class VideoSerializer(serializers.ModelSerializer):

    class Meta:
        model = VideoModel
        fields = ('__all__')