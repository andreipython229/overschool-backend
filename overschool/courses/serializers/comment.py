from common_services.selectel_client import UploadToS3
from courses.models.comments.comment import Comment
from rest_framework import serializers

s3 = UploadToS3()


class CommentSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели комментария
    """

    author_first_name = serializers.CharField(
        source="author.first_name", read_only=True
    )  # Добавляем поле для имени автора
    author_last_name = serializers.CharField(
        source="author.last_name", read_only=True
    )  # Добавляем поле для фамилии автора
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            "id",
            "lesson",
            "author",
            "avatar",
            "author_first_name",
            "author_last_name",
            "content",
            "created_at",
            "public",
            "copy_course_id",
        )
        read_only_fields = (
            "lesson",
            "author",
            "avatar",
            "created_at",
            "copy_course_id",
        )

    def get_author_name(self, obj):
        user = self.context.get("user")
        if user:
            return user.first_name, user.last_name
        else:
            return None

    def get_avatar(self, obj):
        if obj.author.avatar:
            return s3.get_link(obj.author.avatar.name)
        else:
            # Если нет загруженной фотографии, вернуть ссылку на базовую аватарку
            base_avatar_path = "users/avatars/base_avatar.jpg"
            return s3.get_link(base_avatar_path)
