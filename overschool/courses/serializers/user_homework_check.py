from common_services.serializers import AudioFileGetSerializer, TextFileGetSerializer
from courses.models import UserHomeworkCheck
from rest_framework import serializers
from common_services.selectel_client import SelectelClient

s = SelectelClient()


class UserHomeworkCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserHomeworkCheck
        fields = [
            "user_homework_check_id",
            "user_homework",
            "created_at",
            "updated_at",
            "mark",
            "text",
            "status",
            "author",
        ]
        read_only_fields = ["author"]


class UserHomeworkCheckDetailSerializer(serializers.ModelSerializer):
    audio_files = AudioFileGetSerializer(many=True, required=False)
    text_files = TextFileGetSerializer(many=True, required=False)
    author_first_name = serializers.CharField(
        source="author.first_name", read_only=True
    )
    author_last_name = serializers.CharField(source="author.last_name", read_only=True)
    profile_avatar = serializers.SerializerMethodField()

    class Meta:
        model = UserHomeworkCheck
        fields = [
            "user_homework_check_id",
            "user_homework",
            "created_at",
            "updated_at",
            "text",
            "status",
            "mark",
            "author",
            "author_first_name",
            "author_last_name",
            "profile_avatar",
            "text_files",
            "audio_files",
        ]
        read_only_fields = [
            "user_homework",
            "text_files",
            "audio_files",
            "author_first_name",
            "author_last_name",
            "profile_avatar",
            "author",
        ]

    def get_profile_avatar(self, obj):
        if obj.author.profile.avatar:
            return s.get_selectel_link(str(obj.author.profile.avatar))
        else:
            # Если нет загруженной фотографии, вернуть ссылку на базовую аватарку
            base_avatar_path = "/users/avatars/base_avatar.jpg"
            return s.get_selectel_link(base_avatar_path)
