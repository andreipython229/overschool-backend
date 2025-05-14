from courses.models.common.base_lesson import BaseLesson
from courses.models.courses.course import Course
from django.db import models
from users.models import User


class Comment(models.Model):
    """
    Модель для хранения комментариев к уроку
    """

    lesson = models.ForeignKey(
        BaseLesson,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Урок, к которому относится комментарий",
        help_text="Урок, к которому относится комментарий",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Автор комментария",
        help_text="Автор комментария",
    )
    content = models.TextField(
        verbose_name="Содержание комментария",
        help_text="Содержание комментария",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания комментария",
        help_text="Дата создания комментария",
    )
    public = models.BooleanField(
        default=False,
        verbose_name="Опубликован ли комментарий",
        help_text="Опубликован ли комментарий",
    )
    parent_comment = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="replies",
        null=True,
        blank=True,
        verbose_name="Родительский комментарий",
        help_text="Комментарий, на который дается ответ",
    )
    copy_course_id = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name="ID копии курса",
        help_text="ID копии курса, если коммент относится к копии курса",
        blank=True,
        null=True,
        default=None,
    )

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        indexes = [
            models.Index(fields=["lesson"]),
            models.Index(fields=["author"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.author}: {self.content[:50]}..."
