from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models.comments.comment import Comment
from ..serializers.comment import CommentSerializer
from courses.models.common.base_lesson import BaseLesson
from courses.models.lesson.lesson import Lesson
from users.models.user import User
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet


class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint для работы с комментариями к уроку
    """

    def create(self, request, *args, **kwargs):
        """
        Создание нового комментария.
        """

        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        """
        Обновление комментариев по указанному уроку.
        """

        lesson_id = self.request.data.get('lesson_id')
        comments_data = request.data.get('comments', {})

        if not lesson_id:
            return Response({"message": "Не указан lesson_id"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            existing_comments = Comment.objects.filter(lesson_id=lesson_id)
            for comment_id, is_public in comments_data.items():
                comment = existing_comments.filter(id=comment_id).first()
                if comment:
                    comment.public = is_public
                    comment.save()
            return Response(status=status.HTTP_200_OK)
        except BaseLesson.DoesNotExist:
            return Response({"message": "Урок не найден"}, status=status.HTTP_404_NOT_FOUND)

    def list(self, request, *args, **kwargs):
        """
        Получение списка всех комментариев по уроку.
        """

        lesson_id = self.request.GET.get('lesson_id', '')
        try:
            comment = Comment.objects.filter(lesson=lesson_id)
            author_ids = comment.values_list('author_id', flat=True)
            user = User.objects.filter(pk__in=author_ids)
            serializer = CommentSerializer(comment, many=True, context={'user': user})
            comments_data = {'comments': serializer.data}
            return Response(comments_data, status=status.HTTP_200_OK)
        except BaseLesson.DoesNotExist:
            return Response({"message": "Урок не найден"}, status=status.HTTP_404_NOT_FOUND)
