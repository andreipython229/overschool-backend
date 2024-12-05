from common_services.selectel_client import UploadToS3
from rest_framework import serializers
from users.models import Feedback

s3 = UploadToS3()


class FeedbackSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра отзывов о платформе"""

    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = [
            "id",
            "name",
            "surname",
            "position",
            "avatar",
            "content",
            "rating",
            "created_at",
            "updated_at",
        ]

    def validate_rating(self, value):
        """
        Проверяет, чтобы рейтинг был в пределах от 1 до 5 или был пустым.
        """
        if value is not None and (value < 1 or value > 5):
            raise serializers.ValidationError(
                "Рейтинг должен быть от 1 до 5 или пустым."
            )
        return value

    def get_avatar(self, obj):
        if obj.avatar:
            return s3.get_link(obj.avatar.name)
        else:
            # Если нет загруженной фотографии, вернуть ссылку на базовую аватарку
            base_avatar_path = "users/avatars/base_avatar.jpg"
            return s3.get_link(base_avatar_path)
