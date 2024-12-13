from common_services.mixins import LoggingMixin, WithHeadersViewSet
from courses.models.common.base_lesson import BaseLesson
from courses.models.courses.course import Course
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from schools.models import School
from schools.school_mixin import SchoolMixin
from users.models.user import User

from ..models.comments.comment import Comment
from ..serializers.comment import CommentSerializer


class CommentViewSet(WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet):
    """
    API endpoint для работы с комментариями к уроку
    """

    queryset = Comment.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CommentSerializer

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return super().get_permissions()

        elif (
            user.groups.filter(group__name="Teacher", school=school_id).exists()
            or user.groups.filter(group__name="Student", school=school_id).exists()
            or user.email == "student@coursehub.ru"
        ):
            return permissions
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def create(self, request, *args, **kwargs):
        """
        Создание нового комментария.
        """

        author = request.user
        lesson_id = request.data.get("lesson")
        content = request.data.get("content")
        course_id = request.data.get("course_id")

        if lesson_id is None or content is None:
            return Response(
                {"error": "Необходимо указать урок и содержание комментария"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            lesson = BaseLesson.objects.get(id=lesson_id)
        except BaseLesson.DoesNotExist:
            return Response(
                {"error": "Урок с указанным ID не найден"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if course_id:
            try:
                course = Course.objects.get(course_id=course_id)
                if course.is_copy:
                    Comment.objects.create(
                        author=author,
                        lesson=lesson,
                        content=content,
                        copy_course_id=course,
                        public=False,
                    )
                else:
                    Comment.objects.create(
                        author=author, lesson=lesson, content=content, public=False
                    )
            except Course.DoesNotExist:
                return Response(
                    {"error": "Курс с указанным ID не найден"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            # Если course_id не указан, просто создаем комментарий без привязки к курсу
            Comment.objects.create(
                author=author, lesson=lesson, content=content, public=False
            )

        return Response(status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        """
        Обновление комментариев по указанному уроку.
        """

        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        lesson_id = self.request.data.get("lesson_id")
        course_id = self.request.data.get("course_id", "")
        comments_data = self.request.data.get("comments", {})
        user = request.user

        course = Course.objects.get(course_id=course_id)

        if not lesson_id:
            return Response(
                {"message": "Не указан lesson_id"}, status=status.HTTP_400_BAD_REQUEST
            )

        if user.groups.filter(group__name="Admin", school=school_id).exists():
            if course.is_copy:
                existing_comments = Comment.objects.filter(
                    lesson_id=lesson_id, copy_course_id=course
                )
                for comment_id, is_public in comments_data.items():
                    comment = existing_comments.filter(id=comment_id).first()
                    if comment:
                        comment.public = is_public
                        comment.save()
                return Response(status=status.HTTP_200_OK)
            else:
                existing_comments = Comment.objects.filter(lesson_id=lesson_id)
                for comment_id, is_public in comments_data.items():
                    comment = existing_comments.filter(id=comment_id).first()
                    if comment:
                        comment.public = is_public
                        comment.save()
                return Response(status=status.HTTP_200_OK)
        else:
            try:
                existing_comments = Comment.objects.filter(
                    lesson_id=lesson_id, author=user
                )
                for comment_id, is_public in comments_data.items():
                    comment = existing_comments.filter(id=comment_id).first()
                    if comment:
                        comment.public = is_public
                        comment.save()
                return Response(status=status.HTTP_200_OK)
            except Comment.DoesNotExist:
                return Response(
                    {"message": "У вас нет прав для выполнения этого действия."},
                    status=status.HTTP_403_FORBIDDEN,
                )

    def list(self, request, *args, **kwargs):
        """
        Получение списка всех комментариев по уроку.
        """

        lesson_id = self.request.GET.get("lesson_id", "")
        course_id = self.request.GET.get("course_id", "")
        course = Course.objects.get(course_id=course_id)

        if course.is_copy:
            try:
                comment = Comment.objects.filter(
                    lesson=lesson_id, copy_course_id=course
                )
                author_ids = comment.values_list("author_id", flat=True)
                user = User.objects.filter(pk__in=author_ids)
                serializer = CommentSerializer(
                    comment, many=True, context={"user": user}
                )
                comments_data = {"comments": serializer.data}
                return Response(comments_data, status=status.HTTP_200_OK)
            except BaseLesson.DoesNotExist:
                return Response(
                    {"message": "Урок не найден"}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            try:
                comment = Comment.objects.filter(lesson=lesson_id)
                author_ids = comment.values_list("author_id", flat=True)
                user = User.objects.filter(pk__in=author_ids)
                serializer = CommentSerializer(
                    comment, many=True, context={"user": user}
                )
                comments_data = {"comments": serializer.data}
                return Response(comments_data, status=status.HTTP_200_OK)
            except BaseLesson.DoesNotExist:
                return Response(
                    {"message": "Урок не найден"}, status=status.HTTP_404_NOT_FOUND
                )

    @action(detail=False, methods=["POST"])
    def admin_reply_to_comment(self, request, *args, **kwargs):
        """
        Метод для ответа администратора на комментарий.
        Администратор может ответить только один раз на каждый комментарий.
        """
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        user = request.user

        # Проверяем, что пользователь - администратор
        if not user.groups.filter(group__name="Admin", school=school_id).exists():
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

        comment_id = request.data.get("comment_id")
        content = request.data.get("content")

        if not comment_id or not content:
            return Response(
                {
                    "error": "Необходимо указать идентификатор комментария и текст ответа"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            original_comment = Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist:
            return Response(
                {"error": "Комментарий не найден"}, status=status.HTTP_404_NOT_FOUND
            )

        # Проверяем, что администратор еще не отвечал на этот комментарий
        existing_admin_reply = Comment.objects.filter(
            parent_comment=original_comment,
        ).exists()

        if existing_admin_reply:
            return Response(
                {"error": "Вы уже отвечали на этот комментарий"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Создаем ответ администратора
        admin_reply = Comment.objects.create(
            lesson=original_comment.lesson,
            author=user,
            content=content,
            parent_comment=original_comment,
            public=True,  # Ответы администратора всегда публичны
            copy_course_id=original_comment.copy_course_id,
        )

        return Response(
            {"message": "Ответ администратора успешно добавлен"},
            status=status.HTTP_201_CREATED,
        )
