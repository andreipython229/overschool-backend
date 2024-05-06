from common_services.selectel_client import UploadToS3
from common_services.serializers import AudioFileGetSerializer, TextFileGetSerializer
from courses.models import UserHomeworkCheck
from users.models import UserPseudonym
from rest_framework import serializers

s3 = UploadToS3()


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
    author_pseudonym = serializers.SerializerMethodField()
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
            "author_pseudonym",
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
            "author_pseudonym",
            "profile_avatar",
            "author",
        ]

    def get_profile_avatar(self, obj):
        if obj.author.profile.avatar:
            return s3.get_link(obj.author.profile.avatar.name)
        else:
            # Если нет загруженной фотографии, вернуть ссылку на базовую аватарку
            base_avatar_path = "users/avatars/base_avatar.jpg"
            return s3.get_link(base_avatar_path)

    def get_author_pseudonym(self, obj):
        try:
            author = obj.author
            # Проверяем, есть ли у автора псевдоним
            if author:
                author_pseudonym = author.pseudonyms_as_user.get(
                    school=obj.user_homework.homework.section.course.school)
                return author_pseudonym.pseudonym
            else:
                return None
        except UserPseudonym.DoesNotExist:
            return None

