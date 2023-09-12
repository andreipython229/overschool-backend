from rest_framework import serializers

from users.models import Documents


# Serializers define the API representation.
class UploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documents
        fields = "__all__"


# Serializer for multiple files upload.
# class MultipleFilesUploadSerializer(Serializer):
#     file_uploaded = ListField(FileField())
#
#     class Meta:
#         fields = ['file_uploaded']
