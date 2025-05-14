from common_services.selectel_client import UploadToS3
from courses.models.comments.comment import Comment
from rest_framework import serializers

s3 = UploadToS3()


class CommentSerializer(serializers.ModelSerializer):
    """
    Оптимизированный сериализатор модели комментария
    """

    author_first_name = serializers.CharField(source="author.first_name", read_only=True)
    author_last_name = serializers.CharField(source="author.last_name", read_only=True)
    avatar = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

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
            "replies",
        )
        read_only_fields = (
            "lesson",
            "author",
            "avatar",
            "created_at",
            "copy_course_id",
        )

    def get_replies(self, obj):
        """
        Получает ответы на комментарий.
        Используем предварительную загрузку `prefetch_related("replies")`.
        """
        if hasattr(obj, "_cached_replies"):
            replies = obj._cached_replies
        else:
            replies = obj.replies.all()
        return CommentSerializer(replies, many=True).data

    def get_avatar(self, obj):
        """
        Возвращает ссылку на аватар пользователя.
        """
        profile = getattr(obj.author, "profile", None)
        if profile and profile.avatar:
            return s3.get_link(profile.avatar.name)

        # Если у пользователя нет аватарки, возвращаем базовую картинку
        return s3.get_link("users/avatars/base_avatar.jpg")
