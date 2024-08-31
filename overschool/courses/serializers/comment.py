from rest_framework import serializers
from courses.models.comments.comment import Comment


class CommentSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели комментария
    """

    author_first_name = serializers.CharField(source='author.first_name',
                                              read_only=True)  # Добавляем поле для имени автора
    author_last_name = serializers.CharField(source='author.last_name',
                                             read_only=True)  # Добавляем поле для фамилии автора

    class Meta:
        model = Comment
        fields = (
            'id',
            'lesson',
            'author',
            'author_first_name',
            'author_last_name',
            'content',
            'created_at',
            'public',
            'copy_course_id'
        )

    def get_author_name(self, obj):
        user = self.context.get('user')
        if user:
            return user.first_name, user.last_name
        else:
            return None
