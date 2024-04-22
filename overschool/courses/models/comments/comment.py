from django.db import models
from users.models import User
from courses.models.common.base_lesson import BaseLesson


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

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self):
        return f"{self.author}: {self.content[:50]}..."
