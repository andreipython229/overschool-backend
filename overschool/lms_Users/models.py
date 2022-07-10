from ckeditor.fields import RichTextField
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, Permission, PermissionsMixin
from django.db import models
from embed_video.fields import EmbedVideoField

from .database_managers import managers


class TimeStampedModel(models.Model):
    """
    Базовая модель для дополнения остальных полями created_at и updated_at
    """

    created_on = models.DateTimeField(auto_now_add=True, verbose_name="Создано",
                                      help_text="Дата и время, когда запись была создана")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено",
                                      help_text="Дата, когда запись была последний раз обновлена")

    class Meta:
        abstract = True


class Roles(models.Model):
    role = models.CharField(max_length=20, blank=False)
    user_permissions = models.ManyToManyField(Permission)

    def __str__(self):
        return self.role


class MyUserManager(BaseUserManager):

    def _create_user(self, email, username, password, **extra_fields):
        if not email:
            raise ValueError("Вы не ввели Email")
        if not username:
            raise ValueError("Вы не ввели Логин")
        user = self.model(
            email=self.normalize_email(email),
            username=username,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, username, password):
        return self._create_user(email, username, password)

    def create_superuser(self, email, username, password):
        role = Roles.objects.get(id=5)
        return self._create_user(email, username, password, is_staff=True, is_superuser=True, role=role)


# @pgtrigger.register(
#     pgtrigger.Protect(
#         name='set_user_permissions',
#         operation=pgtrigger.Insert | pgtrigger.Update,
#         when=pgtrigger.Before,
#         func=f"UPDATE user SET user_permissions = '{Roles.objects.get()}' WHERE role = '';",
#     )
# )
class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    role = models.ForeignKey(Roles, on_delete=models.CASCADE)
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = MyUserManager()

    def __str__(self):
        return self.username


class Status(models.TextChoices):
    "Варианты статусов для курса"
    UNPUBLISHED = 'НО', 'Не опубликован'
    PUBLISHED = 'О', 'Опубликован'


class Course(TimeStampedModel):
    "Модель курсов"
    course_id = models.AutoField(primary_key=True, editable=False,
                                 verbose_name="Курс ID",
                                 help_text="Уникальный идентификатор курса")
    name = models.CharField(max_length=256, verbose_name="Название курса",
                            help_text="Главное название курса")
    duration_days = models.IntegerField(verbose_name="Продолжительность курса",
                                        help_text="Продолжительность курса в днях")
    status = models.CharField(max_length=256,
                              choices=Status.choices,
                              default=Status.UNPUBLISHED,
                              verbose_name="Статус курса",
                              help_text="Статус курса, отображает состояние курса (опубликован - то сть используется юзерами, не опубликован - это ещё в разработке")
    price = models.DecimalField(max_digits=15, decimal_places=2,
                                verbose_name="Цена",
                                help_text="Цена курса в BYN")
    description = RichTextField(verbose_name="Описание",
                                help_text="Описание курса для отображения, сохраняется в html")
    photo = models.ImageField(upload_to="images/courses/main/", verbose_name="Фотография",
                              help_text="Главная фотография")

    def __str__(self):
        return str(self.course_id)+" "+str(self.name)

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"


class Section(TimeStampedModel):
    "Модель раздела курса"
    section_id = models.AutoField(primary_key=True, editable=False,
                                  verbose_name="ID Раздела",
                                  help_text="Уникальный идентификатор раздела")
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE,
                                  related_name="course_section_id_fk",
                                  verbose_name="ID курса",
                                  help_text="ID курса раздела")
    name = models.CharField(max_length=256, verbose_name="Название курса",
                            help_text="Название раздела курса")
    previous_section_id = models.ForeignKey('self', on_delete=models.PROTECT,
                                            null=True, related_name="section_id_fk",
                                            verbose_name="ID прошлого раздела",
                                            help_text="ID предыдущего курса, если ID None - курс первый")

    objects = managers.SectionManager

    def __str__(self):
        return str(self.section_id)+" "+str(self.name)

    def order(self):
        if self.previous_section_id:
            previous_section: Section = Section.objects.get(section_id=self.previous_section_id)
            return previous_section.order() + 1
        else:
            return 0

    class Meta:
        verbose_name = "Раздел"
        verbose_name_plural = "Разделы"


# Надо добавить очередь
class Lesson(TimeStampedModel):
    "Модель урока в разделе"
    lesson_id = models.AutoField(primary_key=True, editable=False,
                                 verbose_name="ID Урока",
                                 help_text="Уникальный идентификатор урока")
    section_id = models.ForeignKey(Section, on_delete=models.CASCADE,
                                   related_name="section_lesson_id_fk",
                                   verbose_name="ID раздела",
                                   help_text="ID раздела курса")
    name = models.CharField(max_length=256, verbose_name="Название урока",
                            help_text="Название урока")
    description = models.TextField(verbose_name="Описание",
                                   help_text="Описание к уроку")
    video = EmbedVideoField(verbose_name="Видео",
                            help_text="Сюда всталвяем ссылку на видос с ютуба, поэтому сначала его надо загрузить туда")
    previous_lesson_id = models.ForeignKey('self', on_delete=models.PROTECT,
                                           related_name="lesson_id_fk",
                                           verbose_name="Предыдущий урок",
                                           help_text="Предыдущий урок, если None, значит, этот урок первый",
                                           null=True)

    objects = managers.LessonManager

    def __str__(self):
        return str(self.lesson_id)+" "+str(self.name)

    def order(self):
        if self.previous_lesson_id:
            previous_lesson: Lesson = Lesson.objects.get(lesson_id=self.previous_lesson_id)
            return previous_lesson.order() + 1
        else:
            return 0

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"


class Test(TimeStampedModel):
    "Модель теста"
    test_id = models.AutoField(primary_key=True, editable=False,
                               verbose_name="ID Теста",
                               help_text="Уникальный идентификатор теста")
    lesson_id = models.ForeignKey(Lesson, on_delete=models.CASCADE,
                                  related_name="lesson_test_id_fk",
                                  verbose_name="ID урока",
                                  help_text="Урок, после которого идёт данный тест")
    name = models.CharField(max_length=256, verbose_name="Название",
                            help_text="Название теста")
    success_percent = models.IntegerField(verbose_name="Проходной балл",
                                          help_text="Процент правильных ответов для успешно пройденного теста")

    def __str__(self):
        return str(self.test_id)+" "+str(self.name)

    class Meta:
        verbose_name = "Тест"
        verbose_name_plural = "Тесы"


class Question(TimeStampedModel):
    "Модель вопроса в тесте"
    question_id = models.AutoField(primary_key=True, editable=False,
                                   verbose_name="ID Вопроса",
                                   help_text="Уникальный идентификатор вопроса")
    test_id = models.ForeignKey(Test, on_delete=models.CASCADE,
                                related_name="question_test_id_fk",
                                verbose_name="Тест",
                                help_text="Тест, к котрому приввязан вопрос")
    body = RichTextField(verbose_name="Вопрос",
                         help_text="Тело вопроса")

    def __str__(self):
        return str(self.question_id)+" "+str(self.body)

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"


class AnswerStatusChoices(models.TextChoices):
    "Варианты статусов для ответов"
    INCORRECT = 'П', 'Правильный'
    CORRECT = 'Н', 'Неправильный'


class Answer(TimeStampedModel):
    "Модель ответа на вопрос"
    answer_id = models.AutoField(primary_key=True, editable=False,
                                 verbose_name="ID Вопроса",
                                 help_text="Уникальный идентификатор вопроса")
    question_id = models.ForeignKey(Question, on_delete=models.CASCADE,
                                    related_name="question_answer_id_fk",
                                    verbose_name="ID Вопроса",
                                    help_text="Вопрос, к которому привязан ответ")
    body = RichTextField(verbose_name="Тело ответа",
                         help_text="HTML вариант ответа")
    status = models.CharField(max_length=256, choices=AnswerStatusChoices.choices,
                              default=AnswerStatusChoices.INCORRECT,
                              verbose_name="Тип ответа",
                              help_text="Тип ответа: Правильный или неправильный или ещё какой"
                              )

    def __str__(self):
        return str(self.answer_id)+" "+str(self.body)

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"


class Homework(TimeStampedModel):
    "Модель домашнего задания"
    homework_id = models.AutoField(primary_key=True, editable=True,
                                   verbose_name="ID домашнего задания",
                                   help_text="Уникальный идентификатор домашнего задания")
    lesson_id = models.ForeignKey(Lesson, on_delete=models.CASCADE,
                                  related_name="homework_lesson_id_fk",
                                  verbose_name="Домашнее задание",
                                  )
    text = RichTextField(verbose_name="Описание домашнего задания",
                         help_text="HTML вариан описания домашки")
    file = models.FileField(upload_to="media/homework/task/files",
                            verbose_name="Файл домашнего задания",
                            help_text="Файл, в котором хранится вся небходимая информация для домашнего задания")

    def __str__(self):
        return str(self.homework_id)+" Урок: "+str(self.lesson_id)

    class Meta:
        verbose_name = "Домашнее задание"
        verbose_name_plural = "Домашние задания"


class UserHomeworkStatusChoices(models.TextChoices):
    """
    Варианты статусов для ответа на домашнее задание
    """
    ARRIVE = 'ПРИ', 'Пришёл'
    CHECKED = 'ПРО', 'Проверен'
    FAILED = "НЕП", "Неправильно"
    SUCCESS = "ПРА", "Правильно"


class UserHomework(TimeStampedModel):
    """
    Модель выполненной домашки юзером, здесь будут храниться его ответы и комменты препода
    """
    user_homework_id = models.AutoField(primary_key=True, editable=False,
                                        verbose_name="ID выполненного домашнего задания",
                                        help_text="Уникальный идентификатор выполненной домашней работы")
    user_id = models.ForeignKey(User, on_delete=models.SET_DEFAULT,
                                default=1, related_name="user_homework_user_id_fk",
                                verbose_name="ID ученика",
                                help_text="ID ученика, выолнившего домашнюю работу")
    homework_id = models.ForeignKey(Homework, on_delete=models.CASCADE,
                                    related_name="user_homework_homework_id_fk",
                                    verbose_name="ID домашнего задания",
                                    help_text="ID домашнего задания, ответ на который прислали")
    teacher_id = models.ForeignKey(User, on_delete=models.SET_DEFAULT,
                                   default=1, related_name="user_homework_teacher_id_fk",
                                   verbose_name="ID учителя",
                                   help_text="Учитель, который проверял домашнюю работы",
                                   null=True)
    text = models.TextField(verbose_name="Ответ ученика",
                            help_text="Ответ ученика на домашнее задание")
    status = models.CharField(max_length=256, choices=UserHomeworkStatusChoices.choices,
                              default=UserHomeworkStatusChoices.ARRIVE,
                              verbose_name="Статус",
                              help_text="Статус отправленной домашки")
    file = models.FileField(upload_to="media/homework/task/answers",
                            verbose_name="Файл ответа",
                            help_text="Файл, в котором содержится ответ на домашнюю работу")
    mark = models.IntegerField(verbose_name="Отметка",
                               help_text="Отметка за домашнюю работу",
                               null=True, blank=True)
    teacher_message = models.TextField(verbose_name="Комментарий",
                                       help_text="Комментарий преподавателя по проделанной работе",
                                       null=True, blank=True)

    def __str__(self):
        return str(self.user_homework_id)+" "+str(self.user_id)

    class Meta:
        verbose_name = "Сданная домашка"
        verbose_name_plural = "Сданные домашки"


class UserTestStatusChoices(models.TextChoices):
    "Варианты статусов для пройденного теста"
    SUCCESS = 'П', 'Прошёл'
    FAILED = 'Н', 'Не прошёл'


class UserTest(TimeStampedModel):
    "Модель сданнаго теста учеником"
    user_test_id = models.AutoField(primary_key=True, editable=False,
                                    verbose_name="ID сданнаго теста",
                                    help_text="Уникальный идентификатор сданнаго теста")
    test_id = models.ForeignKey(Test, on_delete=models.CASCADE,
                                verbose_name="ID теста", related_name="user_test_test_id_fk",
                                help_text="Уникальный идентификатор теста")
    user_id = models.ForeignKey(User, on_delete=models.SET_DEFAULT,
                                default=1, verbose_name="ID пользователя",
                                related_name="user_test_user_id_fk",
                                help_text="Уникальный идентификатор пользователя")
    success_percent = models.DecimalField(max_digits=10, decimal_places=2,
                                          verbose_name="Процент(%) правильных ответов",
                                          help_text="Процент правильных ответов, которые ввёл ученик ученик")
    status = models.CharField(max_length=256, choices=UserTestStatusChoices.choices,
                              default=UserTestStatusChoices.SUCCESS,
                              verbose_name="Статус",
                              help_text="Статус, отображающий, пройден ли тест учеником")

    class Meta:
        verbose_name = "Сданный тест"
        verbose_name_plural = "Сданные тесты"


class UserProgress(TimeStampedModel):
    """
    Модель для отслеживания прогресса пользователя
    """
    user_id = models.ForeignKey(User, on_delete=models.SET_DEFAULT,
                                default=1, related_name="user_progress_user_id_fk",
                                verbose_name="ID ученика",
                                help_text="ID ученика по прогрессу на курсе")
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE,
                                  related_name="user_progress_course_id_fk",
                                  verbose_name="ID курса",
                                  help_text="ID курса, который сейчас проходит ученик")
    lesson_id = models.ForeignKey(Lesson, on_delete=models.SET_NULL,
                                  related_name="user_progress_lesson_id_fk",
                                  verbose_name="ID урока",
                                  null=True,
                                  help_text="ID курса, на котором сейчас находится ученик, если None значит, урок был удалён, либо ученик только начал")

    class Meta:
        verbose_name = "Надоело писать"
        verbose_name_plural = "Надоело писать 2"


class Chat(TimeStampedModel):
    """
    Модель чата
    """
    chat_id = models.AutoField(primary_key=True, editable=False,
                               verbose_name="ID чата",
                               help_text="Уникальный идентификатор чата")
    admin = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default=1,
                              verbose_name="Админ",
                              help_text="Пользователь, являющийся админом чата, по умолчанию - супер админ")
    participants = models.ManyToManyField(User, related_name='user_chat_mtm',
                                          verbose_name="Пользователи")

    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"


class Message(TimeStampedModel):
    message_id = models.AutoField(primary_key=True, editable=False,
                                  verbose_name="ID сообщения",
                                  help_text="Уникальный идентификатор сообщения")
    user = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default=1,
                             verbose_name="Пользователь",
                             help_text="Пользователь, отправивший сообщение")
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='message_chat_id_fk',
                             verbose_name="ID чата",
                             help_text="Чат, в котором было отправлено это сообщение")
    text = models.TextField(max_length=500, verbose_name="Сообщение",
                            help_text="Сообщение, которое было отправлено пользователем")

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
