import uuid

from common_services.mixins import OrderMixin, TimeStampMixin
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from schools.managers import SchoolManager

User = get_user_model()


class TariffPlan(models.TextChoices):
    "Тарифы для школы"
    JUNIOR = "Junior", "Junior"
    MIDDLE = "Middle", "Middle"
    SENIOR = "Senior", "Senior"


class Tariff(models.Model):
    id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID тарифа",
        help_text="Уникальный идентификатор тарифа",
    )

    name = models.CharField(
        max_length=10, choices=TariffPlan.choices, default=TariffPlan.JUNIOR
    )
    number_of_courses = models.IntegerField(
        null=True, blank=True, verbose_name="Количество курсов"
    )
    number_of_staff = models.IntegerField(
        null=True, blank=True, verbose_name="Количество сотрудников"
    )
    students_per_month = models.IntegerField(
        null=True, blank=True, verbose_name="Количество учеников в месяц"
    )
    total_students = models.IntegerField(
        null=True, blank=True, verbose_name="Общее количество учеников"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")

    @property
    def discount_3_months(self):
        discount = 10  # Скидка при оплате за 3 месяца (в процентах)
        discounted_price = round(float(self.price) * (1 - discount / 100) * 3, 2)
        return discounted_price

    @property
    def discount_6_months(self):
        discount = 20  # Скидка при оплате за 6 месяцев (в процентах)
        discounted_price = round(float(self.price) * (1 - discount / 100) * 6, 2)
        return discounted_price

    @property
    def discount_12_months(self):
        discount = 30  # Скидка при оплате за 12 месяцев (в процентах)
        discounted_price = round(float(self.price) * (1 - discount / 100) * 12, 2)
        return discounted_price

    def __str__(self):
        return f"{self.name} - {self.price}"

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы"
        indexes = [
            models.Index(fields=["name"]),
        ]


class School(TimeStampMixin, OrderMixin):
    """Модель школы"""

    school_id = models.AutoField(
        primary_key=True,
        editable=False,
        verbose_name="ID школы",
        help_text="Уникальный идентификатор школы",
    )
    referral_code = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="Реферальный код",
        help_text="Уникальный реферальный код школы",
    )
    name = models.CharField(
        max_length=256,
        verbose_name="Название",
        help_text="Название школы",
        unique=True,
    )
    tariff = models.ForeignKey(
        Tariff,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Тариф",
        help_text="Тариф школы",
    )
    used_trial = models.BooleanField(
        default=False,
        verbose_name="Пробный тариф использован",
        help_text="Флаг, указывающий, использовал ли пользователь пробный тариф",
    )
    purchased_tariff_end_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Окончание оплаченного тарифа",
        help_text="Дата окончания оплаченного тарифа",
    )
    trial_end_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Дата окончания пробного периода",
        help_text="Дата, когда пробный период истекает",
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="owner_school",
        verbose_name="Владелец школы",
        help_text="ID владельца школы",
    )
    offer_url = models.URLField(
        max_length=200,
        default="",
        blank=True,
        null=True,
        verbose_name="url договора оферты",
    )
    contact_link = models.URLField(
        verbose_name="Ссылка для связи",
        help_text="Ссылка для связи с организатором курса по вопросам записи",
        blank=True,
        null=True,
    )
    test_course = models.BooleanField(
        default=False,
        verbose_name="Включен ли тестовый курс для админов",
        help_text="Включен ли тестовый курс для админов",
    )
    rebranding_enabled = models.BooleanField(
        default=False,
        verbose_name="Ребрендинг активирован",
        help_text="Активировать ребрендинг школы",
    )
    telegram_link = models.URLField(
        verbose_name="Ссылка на Telegram",
        help_text="Ссылка на Telegram",
        blank=True,
        null=True,
    )
    instagram_link = models.URLField(
        verbose_name="Ссылка на Instagram",
        help_text="Ссылка на Instagram",
        blank=True,
        null=True,
    )
    twitter_link = models.URLField(
        verbose_name="Ссылка на Twitter",
        help_text="Ссылка на Twitter",
        blank=True,
        null=True,
    )
    vk_link = models.URLField(
        verbose_name="Ссылка на ВКонтакте",
        help_text="Ссылка на ВКонтакте",
        blank=True,
        null=True,
    )
    youtube_link = models.URLField(
        verbose_name="Ссылка на YouTube",
        help_text="Ссылка на YouTube",
        blank=True,
        null=True,
    )
    extra_link = models.URLField(
        verbose_name="Дополнительная ссылка",
        help_text="Дополнительная ссылка на ресурс",
        blank=True,
        null=True,
    )

    objects = SchoolManager()

    def save(self, *args, **kwargs):
        # Проверка, что тариф не может быть None, пока есть оплаченный или пробный период
        # if self.tariff is None and (
        #     self.purchased_tariff_end_date or self.trial_end_date
        # ):
        #     raise ValidationError(
        #         "Нельзя убрать тариф, пока действует оплаченный или пробный период."
        #     )

        # Отключение ребрендинга, если тариф меняется на другой, не Senior
        if self.tariff and self.tariff.name != TariffPlan.SENIOR:
            self.rebranding_enabled = False

        # Проверка, можно ли включить ребрендинг (доступен только для тарифа Senior и при наличии домена)
        if self.rebranding_enabled:
            if not self.tariff or self.tariff.name != TariffPlan.SENIOR:
                raise ValidationError("Ребрендинг доступен только для тарифа Senior.")
            if not hasattr(self, "domain") or not self.domain:
                raise ValidationError(
                    "Ребрендинг доступен только при наличии собственного домена."
                )

        super().save(*args, **kwargs)

    def check_trial_status(self):
        # Проверка статуса пробного периода
        if (
            self.used_trial
            and self.trial_end_date
            and self.trial_end_date <= timezone.now()
        ):
            self.trial_end_date = None
            self.tariff = None
            self.used_trial = True
        # Проверка оплаты тарифа
        if (
            self.purchased_tariff_end_date
            and self.purchased_tariff_end_date <= timezone.now()
        ):
            self.purchased_tariff_end_date = None
            self.tariff = None

        self.save()

    def __str__(self):
        return str(self.school_id) + " " + str(self.name)

    class Meta:
        verbose_name = "Школа"
        verbose_name_plural = "Школы"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["tariff"]),
            models.Index(fields=["owner"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["order"], name="unique_school_order")
        ]


class SchoolStatistics(models.Model):
    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE,
        verbose_name="Школа",
        related_name="statistics",
    )

    def get_lessons_count(self):
        BaseLesson = apps.get_model("courses", "BaseLesson")
        return BaseLesson.objects.filter(
            section__course__school__name=self.school.name
        ).count()

    def get_last_update_date(self):
        BaseLesson = apps.get_model("courses", "BaseLesson")
        last_lesson = (
            BaseLesson.objects.filter(section__course__school__name=self.school.name)
            .order_by("-updated_at")
            .values("updated_at")
            .first()
        )
        return last_lesson["updated_at"] if last_lesson else None

    def get_completed_lessons_count(self, start_date=None, end_date=None):
        UserProgressLogs = apps.get_model("courses", "UserProgressLogs")
        user_progress_logs = UserProgressLogs.objects.filter(
            completed=True,
            lesson__section__course__school__name=self.school.name,
        )
        if start_date and end_date:
            user_progress_logs = user_progress_logs.filter(
                updated_at__gte=start_date, updated_at__lte=end_date
            )
        if start_date:
            user_progress_logs = user_progress_logs.filter(updated_at__gte=start_date)
        if end_date:
            user_progress_logs = user_progress_logs.filter(updated_at__lte=end_date)

        return user_progress_logs.distinct().count()

    def get_added_students_count(self, start_date=None, end_date=None):
        UserGroup = apps.get_model("users", "UserGroup")
        students_count = UserGroup.objects.filter(
            school__name=self.school.name, group__name="Student"
        )
        if start_date and end_date:
            students_count = students_count.filter(
                created_at__gte=start_date, created_at__lte=end_date
            )
        if start_date:
            students_count = students_count.filter(created_at__gte=start_date)
        if end_date:
            students_count = students_count.filter(created_at__lte=end_date)

        return students_count.distinct().count()

    def __str__(self):
        return f"Статистика для школы {self.school.name}"

    class Meta:
        verbose_name = "Статистика школы"
        verbose_name_plural = "Статистика школ"
        indexes = [
            models.Index(fields=["school"]),
        ]


class SchoolPaymentMethod(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    payment_method = models.CharField(
        max_length=25,
        verbose_name="Метод оплаты",
        help_text="Метод оплаты",
        default=None,
        null=True,
    )
    payment_method_name = models.CharField(
        max_length=100,
        verbose_name="Название метода оплаты",
        help_text="Название метода оплаты",
        default=None,
    )
    account_no = models.CharField(
        unique=True,
        max_length=200,
        verbose_name="Номер лицевого счета",
        help_text="Номер лицевого счета",
        default=None,
        null=True,
        blank=True,
    )
    api_key = models.CharField(
        unique=True,
        max_length=200,
        verbose_name="API-ключ",
        help_text="API-ключ",
        default=None,
    )

    payment_url = models.URLField(
        verbose_name="URL платежного кабинета",
        max_length=250,
        help_text="Ссылка платежного кабинета Продамус",
        default=None,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.payment_method_name} - {self.school}"

    class Meta:
        verbose_name = "Оплата"
        verbose_name_plural = "Оплата"


class SchoolExpressPayLink(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, default=0)
    api_key = models.CharField(
        max_length=200,
        verbose_name="API-ключ",
        help_text="API-ключ",
        default=None,
    )
    payment_method = models.ForeignKey(
        SchoolPaymentMethod,
        on_delete=models.CASCADE,
    )
    invoice_no = models.IntegerField(
        verbose_name="Номер счета", help_text="Номер счета", default=0, null=True
    )
    payment_link = models.CharField(
        max_length=200,
        verbose_name="Ссылка для оплаты",
        help_text="Ссылка для оплаты",
        default=None,
    )
    status = models.CharField(
        max_length=50,
        verbose_name="Статус оплаты",
        help_text="Статус оплаты",
        default=None,
        null=True,
    )
    created = models.DateTimeField(
        verbose_name="Время создания ссылки",
        help_text="Время создания ссылки",
        auto_now_add=True,
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Сумма оплаты",
        help_text="Сумма оплаты",
    )
    currency = models.CharField(
        max_length=3,
        verbose_name="Код валюты",
        help_text="Код валюты",
        default=None,
        null=True,
    )
    first_name = models.CharField(
        max_length=60,
        verbose_name="Имя плательщика",
        help_text="Имя плательщика",
        default=None,
        null=True,
    )
    last_name = models.CharField(
        max_length=60,
        verbose_name="Фамилия плательщика",
        help_text="Фамилия плательщика",
        default=None,
        null=True,
    )
    patronymic = models.CharField(
        max_length=60,
        verbose_name="Отчество плательщика",
        help_text="Отчество плательщика",
        default=None,
        null=True,
    )

    class Meta:
        verbose_name = "Ссылка на оплату"
        verbose_name_plural = "Ссылки на оплату"


class SchoolStudentsTableSettings(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    is_students_grouped = models.BooleanField(
        default=True,
        verbose_name="Сгруппированы ли студенты в таблице",
        help_text="Сгруппированы ли студенты в таблице",
    )

    class Meta:
        verbose_name = "Настройки группировки студентов"
        verbose_name_plural = "Настройки группировки студентов"


@receiver(post_save, sender=School)
def create_school_statistics(sender, instance, created, **kwargs):
    if created:
        SchoolStatistics.objects.create(
            school=instance,
        )


class ProdamusPaymentLink(models.Model):
    """Модель для хранения данных, используемых при формировании платежной ссылки Prodamus"""

    school = models.ForeignKey(School, on_delete=models.CASCADE, default=0)
    school_payment_method = models.ForeignKey(
        SchoolPaymentMethod, on_delete=models.CASCADE
    )
    created = models.DateTimeField(
        verbose_name="Время создания ссылки",
        help_text="Время создания ссылки",
        auto_now_add=True,
    )
    payment_link = models.CharField(
        max_length=700,
        verbose_name="Сформированная ссылка для оплаты",
        help_text="Ссылка для оплаты",
        null=True,
        blank=True,
    )
    api_key = models.CharField(
        max_length=200, verbose_name="API-ключ", help_text="API-ключ", default=""
    )
    do = models.CharField(max_length=20, help_text="Тип действий (link или pay)")
    name = models.CharField(
        max_length=200,
        verbose_name="Наименование товара",
        help_text="Наименование товара",
        default=None,
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Цена товара"
    )
    quantity = models.PositiveIntegerField(help_text="Кол-во товара")
    sys = models.CharField(
        max_length=100,
        verbose_name="код системы интернет-магазина",
        help_text="код системы интернет-магазина",
        null=True,
        blank=True,
    )
    sku = models.CharField(
        max_length=200,
        verbose_name="ID товара в системе интернет-магазин",
        help_text="ID товара в системе интернет-магазин",
        null=True,
        blank=True,
    )

    order_id = models.PositiveIntegerField(
        help_text="Номер заказа в системе интернет-магазина", null=True, blank=True
    )
    customer_phone = models.CharField(
        max_length=20,
        verbose_name="Мобильный телефон клиента",
        help_text="Можно сформировать ссылку на оплату не указывая номер телефона покупателя, он заполнит это поле самостоятельно в окне оплаты",
        null=True,
        blank=True,
    )
    customer_email = models.EmailField(help_text="Email клиента", null=True, blank=True)
    customer_extra = models.TextField(
        null=True, help_text="Дополнительные данные", blank=True
    )
    tax_type = models.PositiveIntegerField(default=0, help_text="Ставка НДС")
    tax_sum = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, help_text="Сумма налога", blank=True
    )
    payment_method = models.CharField(
        max_length=2, help_text="Метод оплаты", null=True, blank=True
    )
    payment_object = models.CharField(
        max_length=2, help_text="Тип оплачиваемой позиции", blank=True
    )
    subscription = models.PositiveIntegerField(
        null=True, help_text="ID подписки", blank=True
    )
    subscription_date_start = models.DateTimeField(
        null=True, help_text="Дата начала подписки", blank=True
    )
    vk_user_id = models.PositiveIntegerField(
        null=True, help_text="ID пользователя VK", blank=True
    )
    vk_user_name = models.CharField(
        max_length=200, null=True, help_text="Имя пользователя VK", blank=True
    )

    urlReturn = models.URLField(
        help_text="URL для возврата пользователя без оплаты", null=True, blank=True
    )
    urlSuccess = models.URLField(
        help_text="URL для возврата пользователя при успешной оплате",
        null=True,
        blank=True,
    )
    urlNotification = models.URLField(
        help_text="URL для уведомления интернет-магазина о поступлении оплаты по заказу. Для того, чтобы система учла этот параметр, также должен быть передан параметр sys",
        null=True,
        blank=True,
    )
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, help_text="Сумма скидки на заказ"
    )
    npd_income_type = models.CharField(
        max_length=20,
        default="FROM_INDIVIDUAL",
        help_text="Тип плательщика",
        blank=True,
    )
    npd_income_inn = models.PositiveIntegerField(
        null=True, help_text="ИНН плательщика", blank=True
    )
    npd_income_company = models.CharField(
        max_length=200, null=True, help_text="Название компании плательщика", blank=True
    )
    link_expired = models.DateTimeField(
        null=True, help_text="Срок действия ссылки", blank=True
    )
    paid_content = models.TextField(
        null=True, help_text="Текст для пользователя после оплаты", blank=True
    )
    ref = models.CharField(
        max_length=40,
        help_text="идентификатор партнера (ПРОМОКОД)",
        null=True,
        blank=True,
    )
    type = models.CharField(
        max_length=40,
        help_text="Если передано значение json, то ответ от Продамуса придет в формате json",
        null=True,
        blank=True,
    )
    callbackType = models.CharField(
        max_length=40,
        help_text="Если передано значение json, то веб-хуки от Продамуса будут приходить в формате json",
        null=True,
        blank=True,
    )
    currency = models.CharField(
        max_length=10,
        help_text="Валюта платежа. Возможные значения: rub, usd, eur, kzt",
        null=True,
        blank=True,
    )
    payments_limit = models.PositiveIntegerField(
        null=True,
        help_text="Лимит оплат по сформированной ссылке",
        verbose_name="Лимит оплат по сформированной ссылке",
        blank=True,
    )
    acquiring = models.CharField(
        max_length=40,
        help_text="Эквайринг.Возможные значения: sbrf, monet, qiwi, xpay, xpaykz",
        null=True,
        verbose_name="Эквайринг",
        blank=True,
    )
    signature = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="Подпись, создаваемая на основе секретного ключа и данных для создания ссылки",
        verbose_name="Подпись запроса",
    )

    class Meta:
        verbose_name = "Ссылка на платеж Prodamus"
        verbose_name_plural = "Ссылки на платежи Prodamus"


class Task(models.TextChoices):
    CREATE_COURSE = "create_course", "Создать свой курс"
    CREATE_FIRST_LESSON = "create_first_lesson", "Создать свой первый урок"
    UPLOAD_VIDEO = "upload_video", "Загрузить видео в урок"
    PUBLISH_COURSE = "publish_course", "Опубликовать курс в каталоге"
    ADD_FIRST_STAFF = "add_first_staff", "Добавить первого сотрудника"
    CREATE_FIRST_GROUP = "create_first_group", "Создать первую группу"
    ADD_FIRST_STUDENT = "add_first_student", "Добавить первого ученика"


class SchoolTask(models.Model):
    """Модель для отслеживания выполнения задач для школы"""

    school = models.ForeignKey(
        "School", on_delete=models.CASCADE, related_name="tasks", verbose_name="Школа"
    )
    task = models.CharField(max_length=50, choices=Task.choices, verbose_name="Задача")
    completed = models.BooleanField(default=False, verbose_name="Выполнено")

    def __str__(self):
        return f"{self.school.name} - {self.get_task_display()} - {'Выполнено' if self.completed else 'Не выполнено'}"

    class Meta:
        unique_together = ("school", "task")
        verbose_name = "Задача для школы"
        verbose_name_plural = "Задачи для школ"
