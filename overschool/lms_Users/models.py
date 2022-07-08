from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, Permission, PermissionsMixin
from django.db import models
from ckeditor.fields import RichTextField
from embed_video.fields import EmbedVideoField


class TimeStampedModel(models.Model):
    "Базовая модель для дополнения остальных полями created_at и updated_at"

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


class Course(TimeStampedModel):
    "Модель курсов"
    course_id = models.AutoField(primary_key=True, editable=True,
                                 verbose_name="Курс ID",
                                 help_text="Уникальный идентификатор курса")

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"

    def save(self, *args, **kwargs):
        course_obj = super(Course, self).save(*args, **kwargs)
        return course_obj


class CourseName(Course):
    "Модель атрибута названия курса"
    # course_id_fk = models.OneToOneField(Course, to_field='course_id',
    #                                     primary_key=True, related_name='course_name_id_fk',
    #                                     on_delete=models.CASCADE, verbose_name="Курс ID",
    #                                     help_text="Уникальный идентификатор курса")
    name = models.CharField(max_length=256, verbose_name="Название курса",
                            help_text="Главное название курса")

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = "Название"
        verbose_name_plural = "Названия"


class CourseDuration(Course):
    "Модель атрибута продолжительности курса"
    # course_id_fk = models.OneToOneField(Course, to_field='course_id',
    #                                     primary_key=True, related_name='course_duration_id_fk',
    #                                     on_delete=models.CASCADE, verbose_name="Курс ID",
    #                                     help_text="Уникальный идентификатор курса")
    duration_days = models.IntegerField(verbose_name="Продолжительность курса",
                                        help_text="Продолжительность курса в днях")

    def __str__(self):
        return str(self.course_id)

    class Meta:
        verbose_name = "Длительность"
        verbose_name_plural = "Длительности"


class Status(models.TextChoices):
    "Варианты статусов для курса"
    UNPUBLISHED = 'НО', 'Не опубликован'
    PUBLISHED = 'О', 'Опубликован'


class CourseStatus(Course):
    "Модель атрибута статуса курса"
    status = models.CharField(max_length=256,
                              choices=Status.choices,
                              default=Status.UNPUBLISHED,
                              verbose_name="Статус курса",
                              help_text="Статус курса, отображает состояние курса (опубликован - то сть используется юзерами, не опубликован - это ещё в разработке")

    def __str__(self):
        return str(self.course_id)

    class Meta:
        verbose_name = "Статус"
        verbose_name_plural = "Статусы"


class CoursePrice(Course):
    "Модель атрибута цены курса"
    price = models.DecimalField(max_digits=15, decimal_places=2,
                                verbose_name="Цена",
                                help_text="Цена курса в BYN")

    def __str__(self):
        return str(self.course_id)

    class Meta:
        verbose_name = "Цена"
        verbose_name_plural = "Цены"


class CourseDescription(Course):
    "Модель атрибута описания курса"
    description = RichTextField(verbose_name="Описание",
                                help_text="Описание курса для отображения, сохраняется в html")

    def __str__(self):
        return str(self.course_id)

    class Meta:
        verbose_name = "Описание курса"
        verbose_name_plural = "Описания курсов"


class CoursePhoto(Course):
    "Модель атрибута фотографии курса"
    photo = models.ImageField(upload_to="images/courses/main/", verbose_name="Фотография",
                              help_text="Главная фотография")

    def __str__(self):
        return str(self.course_id)

    class Meta:
        verbose_name = "Фото"
        verbose_name_plural = "Фото"


class Section(TimeStampedModel):
    "Модель раздела курса"
    section_id = models.AutoField(primary_key=True, editable=True,
                                 verbose_name="ID Раздела",
                                 help_text="Уникальный идентификатор раздела")
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE,
                                     related_name="course_section_id_fk",
                                     verbose_name="ID курса",
                                     help_text="ID курса раздела")


class SectionName(Section):
    "Модель атрибута названия раздела"
    name = models.CharField(max_length=256, verbose_name="Название курса",
                            help_text="Название раздела курса")


class Lesson(TimeStampedModel):
    "Модель урока в разделе"
    lesson_id = models.AutoField(primary_key=True, editable=True,
                                 verbose_name="ID Урока",
                                 help_text="Уникальный идентификатор урока")
    section_id = models.ForeignKey(Section, on_delete=models.CASCADE,
                                      related_name="section_lesson_id_fk",
                                      verbose_name="ID раздела",
                                      help_text="ID раздела курса")


class LessonName(Lesson):
    "Модель атрибута названия урока"
    name = models.CharField(max_length=256, verbose_name="Название урока",
                            help_text="Название урока")


class LessonDescription(Lesson):
    "Модель атрибута описания урока"
    description = models.TextField(verbose_name="Описание",
                                   help_text="Описание к уроку")


class LessonVideo(Lesson):
    "Модель атрибута видео урока"
    video = EmbedVideoField(verbose_name="Видео",
                            help_text="Сюда всталвяем ссылку на видос с ютуба, поэтому сначала его надо загрузить туда")


class Test(TimeStampedModel):
    "Модель теста"
    test_id = models.AutoField(primary_key=True, editable=True,
                               verbose_name="ID Теста",
                               help_text="Уникальный идентификатор теста")
    lesson_id = models.ForeignKey(Lesson, on_delete=models.CASCADE,
                                  related_name="lesson_test_id_fk",
                                  verbose_name="ID урока",
                                  help_text="Урок, после которого идёт данный тест")


class TestName(Test):
    "Модель атрибута названия теста"
    name = models.CharField(max_length=256, verbose_name="Название",
                            help_text="Название теста")


class Question(TimeStampedModel):
    "Модель вопроса в тесте"
    question_id = models.AutoField(primary_key=True, editable=True,
                                    verbose_name="ID Вопроса",
                                    help_text="Уникальный идентификатор вопроса")
    test_id = models.ForeignKey(Test, on_delete=models.CASCADE,
                                related_name="question_test_id_fk",
                                verbose_name="Тест",
                                help_text="Тест, к котрому приввязан вопрос")


class QuestionBody(Question):
    "Модель атрибута тела вопроса"
    body = RichTextField(verbose_name="Вопрос",
                         help_text="Тело вопроса")


class Answer(TimeStampedModel):
    "Модель ответа на вопрос"
    answer_id = models.AutoField(primary_key=True, editable=True,
                                 verbose_name="ID Вопроса",
                                 help_text="Уникальный идентификатор вопроса")
    question_id = models.ForeignKey(Question, on_delete=models.CASCADE,
                                    related_name="question_answer_id_fk",
                                    verbose_name="ID Вопроса",
                                    help_text="Вопрос, к которому привязан ответ")


class AnswerBody(Answer):
    "Модель тела ответа"
    body = RichTextField(verbose_name="Тело ответа",
                         help_text="HTML вариант ответа")


class AnswerStatusChoices(models.TextChoices):
    "Варианты статусов для ответов"
    INCORRECT = 'П', 'Правильный'
    CORRECT = 'Н', 'Неправильный'


class AnswerStatus(Answer):
    "Модель тела статуса"
    status = models.CharField(max_length=256, choices=AnswerStatusChoices.choices,
                              default=AnswerStatusChoices.INCORRECT,
                              verbose_name="Тип ответа",
                              help_text="Тип ответа: Правильный или неправильный или ещё какой"
                              )


class Homework(TimeStampedModel):
    "Модель домашнего задания"
    homework_id = models.AutoField(primary_key=True, editable=True,
                                   verbose_name="ID домашнего задания",
                                   help_text="Уникальный идентификатор домашнего задания")
    lesson_id = models.ForeignKey(Lesson, on_delete=models.CASCADE,
                                  related_name="homework_lesson_id_fk",
                                  verbose_name="Домашнее задание",
                                  )


class TextHomework(Homework):
    "Модель атрибута текста к доммашнему заданию"
    text = RichTextField(verbose_name="Описание домашнего задания",
                         help_text="HTML вариан описания домашки")


class FileHomeWork(Homework):
    "Модель атрибута файла к домашке"
    file = models.FileField(upload_to="media/homework/task/files",
                            verbose_name="Файл домашнего задания",
                            help_text="Файл, в котором хранится вся небходимая информация для домашнего задания")


class UserHomework(TimeStampedModel):
    "Модель выполненной домашки юзером, здесь будут храниться его ответы и комменты препода"
    user_homework_id = models.AutoField(primary_key=True, editable=True,
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


class TextUserHomeWork(UserHomework):
    "Модель атрибута текста, который прислал ученик в ответ на домашнее задание"
    text = models.TextField(verbose_name="Ответ ученика",
                            help_text="Ответ ученика на домашнее задание")


class UserHomeworkStatusChoices(models.TextChoices):
    "Варианты статусов для ответа на домашнее задание"
    ARRIVE = 'ПРИ', 'Пришёл'
    CHECKED = 'ПРО', 'Проверен'
    FAILED = "НЕП", "Неправильно"
    SUCCESS = "ПРА", "Правильно"


class StatusUserHomework(UserHomework):
    "Модель атрибута статуса домашнего задания"
    status = models.CharField(max_length=256, choices=UserHomeworkStatusChoices.choices,
                              default=UserHomeworkStatusChoices.ARRIVE,
                              verbose_name="Статус",
                              help_text="Статус отправленной домашки")


class FileUserHomeWork(UserHomework):
    "Модель атрибута файла к отправленной домашке"
    file = models.FileField(upload_to="media/homework/task/answers",
                            verbose_name="Файл ответа",
                            help_text="Файл, в котором содержится ответ на домашнюю работу")


class MarkUserHomework(UserHomework):
    "Модель атрибута отметки на домашнее задание"
    mark = models.IntegerField(verbose_name="Отметка",
                               help_text="Отметка за домашнюю работу",
                               null=True)


class TeacherMessageUserHomeWork(UserHomework):
    "Модель атрибута комментария от учителя"
    teacher_message = models.TextField(verbose_name="Комментарий",
                                       help_text="Комментарий преподавателя по проделанной работе",
                                       null=True)


class UserTest(TimeStampedModel):
    "Модель сданнаго теста учеником"
    user_test_id = models.AutoField(primary_key=True, editable=True,
                                    verbose_name="ID сданнаго теста",
                                    help_text="Уникальный идентификатор сданнаго теста")
    test_id = models.ForeignKey(Test, on_delete=models.CASCADE,
                                verbose_name="ID теста", related_name="user_test_test_id_fk",
                                help_text="Уникальный идентификатор теста")
    user_id = models.ForeignKey(User, on_delete=models.SET_DEFAULT,
                                default=1, verbose_name="ID пользователя",
                                related_name="user_test_user_id_fk",
                                help_text="Уникальный идентификатор пользователя")


class MarkUserTest(UserTest):
    "Модель атрибута отметки за пройденный тест"
    mark = models.DecimalField(max_digits=10, decimal_places=2,
                               verbose_name="Отметка за тест",
                               help_text="Отметка за пройденный тест")


class UserProgress(TimeStampedModel):
    pass