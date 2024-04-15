from common_services.selectel_client import UploadToS3
from courses.models import BaseLessonBlock, BlockButton
from rest_framework import serializers

s3 = UploadToS3()


class BlockButtonSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockButton
        fields = [
            "id",
            "block",
            "name",
            "link",
            "color",
        ]

    def validate(self, data):
        instance = getattr(self, "instance", None)
        block = data.get("block")

        if block and instance is None:
            existing_buttons_count = BlockButton.objects.filter(block=block).count()
            if existing_buttons_count >= 4:
                raise serializers.ValidationError(
                    "Больше добавлять нельзя, в блоке уже 4 кнопки есть"
                )
        return data


class LessonBlockSerializer(serializers.ModelSerializer):

    buttons = BlockButtonSerializer(required=False, many=True)

    class Meta:
        model = BaseLessonBlock
        fields = [
            "id",
            "base_lesson",
            "video",
            "url",
            "description",
            "code",
            "language",
            "picture",
            "type",
            "formula",
            "buttons",
            "order",
        ]
        read_only_fields = ["order"]

    def validate(self, data):
        instance = getattr(self, "instance", None)
        base_lesson = data.get("base_lesson")
        video = data.get("video")
        url = data.get("url")
        description = data.get("description")
        code = data.get("code")
        picture = data.get("picture")
        formula = data.get("formula")

        fields_to_check = [video, url, description, code, picture, formula]

        non_empty_fields = [field for field in fields_to_check if field is not None]
        if len(non_empty_fields) > 1:
            raise serializers.ValidationError("Можно указать только одно поле")

        if base_lesson and instance is None:
            existing_blocks_count = BaseLessonBlock.objects.filter(
                base_lesson=base_lesson
            ).count()
            if existing_blocks_count >= 10:
                raise serializers.ValidationError(
                    "Больше добавлять нельзя, уже 10 блоков"
                )

        return data


class BlockDetailSerializer(serializers.ModelSerializer):
    video = serializers.SerializerMethodField()
    picture_url = serializers.SerializerMethodField()
    buttons = BlockButtonSerializer(required=False, many=True)

    class Meta:
        model = BaseLessonBlock
        fields = [
            "id",
            "video",
            "url",
            "description",
            "code",
            "language",
            "picture",
            "picture_url",
            "formula",
            "buttons",
            "order",
            "type",
        ]
        read_only_fields = ["order"]

    def get_video(self, obj):
        return s3.get_link(obj.video.name) if obj.video else None

    def get_picture_url(self, obj):
        return s3.get_link(obj.picture.name) if obj.picture else None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get("code") is None and instance.type != "code":
            del data["code"]
            del data["language"]
        if data.get("url") is None and instance.type != "video":
            del data["url"]
        if data.get("description") is None and instance.type != "description":
            del data["description"]
        if data.get("picture") is None and instance.type != "picture":
            del data["picture"]
            del data["picture_url"]
        if data.get("video") is None and instance.type != "video":
            del data["video"]
        if data.get("formula") is None and instance.type != "formula":
            del data["formula"]
        if not len(data.get("buttons")) and instance.type != "buttons":
            del data["buttons"]
        return data


class BlockUpdateSerializer(serializers.ModelSerializer):
    file_use = serializers.BooleanField(required=False)

    class Meta:
        model = BaseLessonBlock
        fields = [
            "video",
            "url",
            "description",
            "code",
            "language",
            "picture",
            "formula",
            "file_use",
        ]

    def validate(self, data):
        video = data.get("video")
        url = data.get("url")
        description = data.get("description")
        code = data.get("code")
        picture = data.get("picture")
        formula = data.get("formula")

        fields_to_check = [video, url, description, code, picture, formula]

        non_empty_fields = [field for field in fields_to_check if field is not None]
        if len(non_empty_fields) > 1:
            raise serializers.ValidationError("Можно указать только одно поле")

        return data


class LessonOrderSerializer(serializers.Serializer):
    block_id = serializers.IntegerField()
    order = serializers.IntegerField()
