from common_services.selectel_client import UploadToS3
from rest_framework import serializers
from schools.models import SchoolDocuments

s3 = UploadToS3()


class SchoolDocumentsSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели документов школы
    """

    class Meta:
        model = SchoolDocuments
        fields = [
            "id",
            "user",
            "school",
            "stamp",
            "signature",
        ]


class SchoolDocumentsDetailSerializer(serializers.ModelSerializer):
    stamp = serializers.SerializerMethodField()
    signature = serializers.SerializerMethodField()

    class Meta:
        model = SchoolDocuments
        fields = [
            "id",
            "user",
            "school",
            "stamp",
            "signature",
        ]

    def get_stamp(self, obj):
        return s3.get_link(obj.stamp.name) if obj.stamp else None

    def get_signature(self, obj):
        return s3.get_link(obj.signature.name) if obj.signature else None


class SchoolDocumentsUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolDocuments
        fields = [
            "stamp",
            "signature",
        ]
