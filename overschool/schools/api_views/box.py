import random
import uuid
from datetime import timedelta

import requests
from common_services.mixins import WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from django.db.models import F, Sum
from django.utils.timezone import now
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from schools.models import (
    Box,
    BoxPrize,
    Payment,
    Prize,
    School,
    SchoolPaymentMethod,
    UserBox,
    UserPrize,
)
from schools.school_mixin import SchoolMixin
from schools.serializers import (
    BoxDetailSerializer,
    BoxPrizeSerializer,
    BoxSerializer,
    PaymentSerializer,
    PrizeDetailSerializer,
    PrizeSerializer,
    UserBoxSerializer,
    UserPrizeSerializer,
)

s3 = UploadToS3()


class BoxViewSet(WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet):
    serializer_class = BoxSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return permissions
        if self.action in [
            "list",
            "retrieve",
        ]:
            # Разрешения для просмотра курсов (любой пользователь школы)
            if (
                user.groups.filter(
                    group__name__in=["Student", "Teacher"], school=school_id
                ).exists()
                or user.email == "student@coursehub.ru"
            ):
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return BoxDetailSerializer
        return BoxSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Box.objects.none()  # Возвращаем пустой queryset при генерации схемы
        user = self.request.user
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        if (
            user.groups.filter(
                group__name__in=["Student", "Teacher"], school=school_id
            ).exists()
            or user.email == "student@coursehub.ru"
        ):
            return Box.objects.filter(school=school_id, is_active=True)
        return Box.objects.filter(school=school_id)

    def create(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        icon = (
            s3.upload_school_image(request.FILES["icon"], school_id)
            if request.FILES.get("icon")
            else None
        )
        box = serializer.save(icon=icon, school=School.objects.get(school_id=school_id))
        serializer = BoxDetailSerializer(box)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        box = self.get_object()
        school_id = box.school.school_id
        serializer = self.get_serializer(box, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if request.FILES.get("icon"):
            if box.icon:
                s3.delete_file(str(box.icon))
            serializer.validated_data["icon"] = s3.upload_school_image(
                request.FILES["icon"], school_id
            )
        else:
            serializer.validated_data["icon"] = box.icon
        self.perform_update(serializer)
        serializers = BoxDetailSerializer(box)

        return Response(serializers.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        box = self.get_object()
        self.perform_destroy(box)
        remove_resp = []
        if box.icon:
            remove_resp.append(s3.delete_file(str(box.icon)))

        if "Error" in remove_resp:
            return Response(
                {"error": "Ошибка удаления ресурса из хранилища Selectel"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["patch"])
    def bulk_update(self, request, *args, **kwargs):
        """
        Обновляет несколько коробок.
        """
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        if not isinstance(request.data, list):
            return Response(
                {"error": "Ожидался массив с данными для обновления."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_boxes = []
        for box_data in request.data:
            box_id = box_data.pop("id", None)
            if not box_id:
                return Response(
                    {"error": "ID коробки обязателен для обновления."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                box = Box.objects.get(id=box_id, school_id=school_id)
                serializer = self.get_serializer(box, data=box_data, partial=True)
                serializer.is_valid(raise_exception=True)
                if "icon" in request.FILES:
                    if box.icon:
                        s3.delete_file(str(box.icon))
                    serializer.validated_data["icon"] = s3.upload_school_image(
                        request.FILES["icon"], school_id
                    )
                else:
                    serializer.validated_data["icon"] = box.icon
                self.perform_update(serializer)
                updated_boxes.append(BoxDetailSerializer(box).data)
            except Box.DoesNotExist:
                continue

        return Response(updated_boxes, status=status.HTTP_200_OK)

    @action(detail=False, methods=["delete"])
    def bulk_delete(self, request, *args, **kwargs):
        """
        Удаляет несколько коробок.
        """
        box_ids = request.data.get("ids", None)
        if not box_ids or not isinstance(box_ids, list):
            return Response(
                {"error": "Ожидался массив ID коробок для удаления."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        boxes = Box.objects.filter(id__in=box_ids)
        remove_responses = []
        for box in boxes:
            if box.icon:
                remove_responses.append(s3.delete_file(str(box.icon)))
            box.delete()

        if "Error" in remove_responses:
            return Response(
                {"error": "Ошибка удаления некоторых ресурсов из хранилища Selectel."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"message": "Коробки успешно удалены."}, status=status.HTTP_204_NO_CONTENT
        )


class PrizeViewSet(WithHeadersViewSet, SchoolMixin, viewsets.ModelViewSet):
    serializer_class = PrizeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        permissions = super().get_permissions()
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        if user.groups.filter(group__name="Admin", school=school_id).exists():
            return permissions
        if self.action in ["list", "retrieve"]:
            # Разрешения для просмотра призов (любой пользователь школы)
            if user.groups.filter(
                group__name__in=["Student", "Teacher"], school=school_id
            ).exists():
                return permissions
            else:
                raise PermissionDenied("У вас нет прав для выполнения этого действия.")
        else:
            raise PermissionDenied("У вас нет прав для выполнения этого действия.")

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return PrizeDetailSerializer
        return PrizeSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return (
                Prize.objects.none()
            )  # Возвращаем пустой queryset при генерации схемы
        user = self.request.user
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
        if user.groups.filter(
            group__name__in=["Student", "Teacher"], school=school_id
        ).exists():
            return Prize.objects.filter(school=school_id, is_active=True)
        return Prize.objects.filter(school=school_id)

    def perform_active_check(self, prize):
        """
        Добавление/удаление приза в коробки в зависимости от статуса `is_active`.
        """
        if prize.is_active:
            # Если приз активный, добавляем его во все коробки
            boxes = Box.objects.filter(school=prize.school)
            for box in boxes:
                BoxPrize.objects.get_or_create(box=box, prize=prize)
        else:
            # Если приз неактивный, удаляем его из всех коробок
            BoxPrize.objects.filter(prize=prize).delete()

    def create(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Загружаем иконку в S3
        icon = (
            s3.upload_school_image(request.FILES["icon"], school_id)
            if request.FILES.get("icon")
            else None
        )

        # Создаем приз
        prize = serializer.save(
            icon=icon, school=School.objects.get(school_id=school_id)
        )

        # Проверяем активность и обновляем коробки
        self.perform_active_check(prize)

        serializer = PrizeDetailSerializer(prize)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        prize = self.get_object()
        school_id = prize.school.school_id

        serializer = self.get_serializer(prize, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Обновляем иконку в S3, если она передана
        if request.FILES.get("icon"):
            if prize.icon:
                s3.delete_file(str(prize.icon))
            serializer.validated_data["icon"] = s3.upload_school_image(
                request.FILES["icon"], school_id
            )

        # Обновляем объект
        self.perform_update(serializer)

        # Проверяем активность и обновляем коробки
        self.perform_active_check(prize)

        serializer = PrizeDetailSerializer(prize)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        prize = self.get_object()
        self.perform_destroy(prize)

        # Удаляем иконку из S3
        if prize.icon:
            s3.delete_file(str(prize.icon))

        return Response(status=status.HTTP_204_NO_CONTENT)


class PaymentLinkSerializer(serializers.Serializer):
    pass


class CreatePaymentLinkView(WithHeadersViewSet, SchoolMixin, APIView):
    """
    Эндпоинт для создания ссылки на оплату коробки.
    """

    serializer_class = PaymentLinkSerializer

    def post(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        data = request.data
        user = self.request.user
        try:
            # Проверяем наличие всех обязательных данных
            required_fields = ["box_id"]
            for field in required_fields:
                if field not in data:
                    return Response(
                        {"error": f'Поле "{field}" обязательно'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Проверяем существование коробки
            box = Box.objects.get(id=data["box_id"])

            # Создаем объект Payment
            payment = Payment.objects.create(
                user=user,
                box=box,
                school=school,
                amount=box.price,
                invoice_no=0,  # Номер счета будет обновлен после генерации
                payment_status="pending",
            )

            # Генерация ссылки через API ExpressPay
            payment_method = SchoolPaymentMethod.objects.get(school=school)
            token = payment_method.api_key
            api_url = f"https://api.express-pay.by/v1/invoices?token={token}"
            account_no = f"{payment.id}-{payment.user.id}-{int(payment.created_at.timestamp())}-{uuid.uuid4().hex[:6]}"

            payload = {
                "Token": token,
                "AccountNo": account_no,
                "Amount": payment.amount,
                "Currency": 933,
                "Info": f"Оплата {box.name}",
                "ReturnInvoiceUrl": 1,
            }

            response = requests.post(api_url, data=payload)
            if response.status_code != 200:
                payment.delete()
                return Response(
                    {"error": "Не удалось создать ссылку на оплату"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            result = response.json()
            payment.invoice_no = result.get("InvoiceNo")
            payment.save()

            return Response(
                {"payment_link": result.get("InvoiceUrl")},
                status=status.HTTP_201_CREATED,
            )

        except Box.DoesNotExist:
            return Response(
                {"error": "Коробка не найдена"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CheckPaymentSerializer(serializers.Serializer):
    pass


class CheckPaymentStatusView(WithHeadersViewSet, SchoolMixin, APIView):
    """
    Эндпоинт для проверки статусов платежей, ожидающих оплаты.
    """

    serializer_class = CheckPaymentSerializer

    def get(self, request, *args, **kwargs):
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        user = request.user

        # Извлечение параметров фильтрации
        payment_status = request.query_params.get("payment_status")
        user_id = request.query_params.get("user_id")

        try:
            # Фильтруем платежи для проверки статуса
            if user.groups.filter(
                group__name="Admin", school=school.school_id
            ).exists():
                payments_to_check = Payment.objects.filter(
                    school=school, payment_status="pending"
                )
            else:
                payments_to_check = Payment.objects.filter(
                    user=user, school=school, payment_status="pending"
                )
            updated_payments = []

            for payment in payments_to_check:
                # Формируем URL для проверки статуса
                url = f"https://api.express-pay.by/v1/invoices/{payment.invoice_no}/status"
                payment_method = SchoolPaymentMethod.objects.get(school=school)
                token = payment_method.api_key

                if now() - payment.created_at >= timedelta(minutes=30):
                    # Удаляем счет через API ExpressPay
                    delete_url = f"https://api.express-pay.by/v1/invoices/{payment.invoice_no}?token={token}"
                    delete_response = requests.delete(delete_url)
                    if delete_response.status_code == 200:
                        # Если удаление прошло успешно, помечаем платеж как "failed"
                        payment.payment_status = "failed"
                        payment.save()

                # Отправляем GET-запрос в ExpressPay API
                response = requests.get(f"{url}?token={token}")

                if response.status_code == 200:
                    status_code = response.json().get("Status")

                    # Обновляем статус платежа на основании кода статуса
                    if status_code == 3 or status_code == 6:  # Успешно оплачено
                        payment.payment_status = "completed"
                        total_boxes = payment.box.quantity + payment.box.bonus_quantity
                        user_box, created = UserBox.objects.get_or_create(
                            user=payment.user, box=payment.box
                        )
                        user_box.unopened_count += total_boxes
                        user_box.save()
                    elif (
                        status_code == 2 or status_code == 5
                    ):  # Просрочено или отменено
                        payment.payment_status = "failed"
                    # Сохраняем только измененные платежи
                    payment.save()
                    updated_payments.append(payment)

            # Фильтруем платежи для проверки статусов
            if user.groups.filter(
                group__name="Admin", school=school.school_id
            ).exists():
                # Фильтрация для администратора
                all_payments = Payment.objects.filter(school=school)
                if user_id:
                    all_payments = all_payments.filter(user=user_id)
                if payment_status:
                    all_payments = all_payments.filter(payment_status=payment_status)
            else:
                # Фильтрация для обычного пользователя
                all_payments = Payment.objects.filter(user=user, school=school)
                if payment_status:
                    all_payments = all_payments.filter(payment_status=payment_status)

            serializer = PaymentSerializer(all_payments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


def open_box(user, box):
    """
    Логика открытия одной коробки пользователем.
    """
    # Получаем связь UserBox
    user_box = UserBox.objects.get(user=user, box=box)

    if user_box.unopened_count <= 0:
        raise ValueError("У вас нет неоткрытых коробок.")

    # Уменьшаем количество неоткрытых коробок
    user_box.unopened_count -= 1
    user_box.opened_count += 1
    user_box.save()

    # Считаем общее количество открытых коробок пользователя по всем коробкам
    total_opened_count = (
        UserBox.objects.filter(user=user, box__school=box.school).aggregate(
            total_opened=Sum("opened_count")
        )["total_opened"]
        or 0
    )

    # Проверяем гарантированный приз
    guaranteed_prize = None
    for box_prize in BoxPrize.objects.filter(
        box=box, prize__guaranteed_box_count__isnull=False
    ):
        guaranteed_count = box_prize.prize.guaranteed_box_count

        # Проверяем, что гарантированное количество больше 0
        if guaranteed_count and guaranteed_count > 0:
            if total_opened_count % guaranteed_count == 0:
                guaranteed_prize = box_prize.prize
                break

    # Если гарантированный приз найден, выдается он
    if guaranteed_prize:
        return UserPrize.objects.create(user=user, prize=guaranteed_prize)

    # Если гарантированный приз не найден, рассчитываем случайный
    box_prizes = BoxPrize.objects.filter(box=box)
    total_prize_chance = sum(bp.prize.drop_chance for bp in box_prizes)

    # Нормализация шансов
    normalized_prizes = []
    for box_prize in box_prizes:
        normalized_prizes.append(
            {
                "prize": box_prize.prize,
                "chance": box_prize.prize.drop_chance,  # Используем оригинальные шансы
            }
        )

    # Добавляем шанс "ничего не выиграть", если общая сумма шансов < 100
    empty_chance = 100 - total_prize_chance
    if empty_chance > 0:
        normalized_prizes.append({"prize": None, "chance": empty_chance})

    # Генерируем случайное число
    roll = random.uniform(0, 100)
    current = 0

    # Проверяем выпадение призов
    for prize_data in normalized_prizes:
        current += prize_data["chance"]
        if roll <= current:
            if prize_data["prize"] is None:
                # Ничего не выиграл
                return None
            return UserPrize.objects.create(user=user, prize=prize_data["prize"])

    # Безопасный возврат на случай ошибок
    return None


class OpenBoxSerializer(serializers.Serializer):
    pass


class OpenBoxView(WithHeadersViewSet, SchoolMixin, APIView):
    serializer_class = OpenBoxSerializer

    def get(self, request, *args, **kwargs):
        """
        Возвращает все купленные пользователем коробки с их состоянием,
        где еще остались неоткрытые коробки.
        """
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)
        user = request.user

        # Фильтруем коробки, где есть неоткрытые
        user_boxes = UserBox.objects.filter(
            user=user, box__school=school, unopened_count__gt=0
        )

        # Добавляем поле "до гарантированного приза"
        total_opened_count = (
            UserBox.objects.filter(user=user, box__school=school).aggregate(
                total_opened=Sum("opened_count")
            )["total_opened"]
            or 0
        )

        for user_box in user_boxes:
            guaranteed_count = (
                BoxPrize.objects.filter(
                    box=user_box.box, prize__guaranteed_box_count__isnull=False
                )
                .values_list("prize__guaranteed_box_count", flat=True)
                .first()
            )
            if guaranteed_count:
                user_box.remaining_to_guarantee = guaranteed_count - (
                    total_opened_count % guaranteed_count
                )
            else:
                user_box.remaining_to_guarantee = None

        serializer = UserBoxSerializer(
            user_boxes,
            many=True,
            context={"remaining_to_guarantee": total_opened_count},
        )
        return Response(serializer.data, status=200)

    def post(self, request, box_id, *args, **kwargs):
        """
        Открытие коробки пользователем.
        """
        user = request.user
        try:
            box = Box.objects.get(id=box_id)
            user_prize = open_box(user, box)

            if not user_prize:
                return Response({"message": "Вы ничего не выиграли"}, status=200)

            # Сериализация выпавшего приза
            prize_serializer = PrizeDetailSerializer(user_prize.prize)

            return Response(
                {
                    "message": f"Вы открыли коробку и получили приз: {user_prize.prize.name}",
                    "prize": prize_serializer.data,
                },
                status=200,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    def get_prizes(self, request, *args, **kwargs):
        """
        Возвращает все призы, полученные пользователем.
        Администратор школы видит призы всех пользователей школы с фильтром по пользователю и статусу.
        Пользователь видит свои призы с фильтром по статусу.
        """
        user = request.user
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)

        try:
            # Получаем параметры фильтрации
            user_id = request.query_params.get("user_id")
            is_used = request.query_params.get("is_used")

            # Преобразуем `is_used` в boolean, если передан
            if is_used is not None:
                is_used = is_used.lower() == "true"

            # Проверяем роль пользователя
            if user.groups.filter(
                group__name="Admin", school=school.school_id
            ).exists():
                # Администратор школы: видит все призы школы
                user_prizes = UserPrize.objects.filter(prize__school=school)
                if user_id:
                    user_prizes = user_prizes.filter(user=user_id)
                if is_used is not None:
                    user_prizes = user_prizes.filter(is_used=is_used)
            else:
                # Пользователь: видит только свои призы
                user_prizes = UserPrize.objects.filter(user=user, prize__school=school)
                if is_used is not None:
                    user_prizes = user_prizes.filter(is_used=is_used)

            serializer = UserPrizeSerializer(user_prizes, many=True)
            return Response(serializer.data, status=200)

        except School.DoesNotExist:
            return Response({"error": "Школа не найдена"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def update_prize_status(self, request, prize_id, *args, **kwargs):
        """
        Обновляет статус использования приза (is_used).
        """
        user = request.user
        school_name = self.kwargs.get("school_name")
        school = School.objects.get(name=school_name)

        try:
            # Проверяем, является ли пользователь администратором школы
            if not user.groups.filter(
                group__name="Admin", school=school.school_id
            ).exists():
                raise PermissionDenied("Вы не имеете права обновлять статус приза.")

            # Получаем приз пользователя
            user_prize = UserPrize.objects.filter(
                prize__school=school, id=prize_id
            ).first()
            if not user_prize:
                raise NotFound("Приз не найден.")

            # Обновляем статус is_used
            user_prize.is_used = True
            user_prize.save()

            return Response(
                {
                    "message": f"Статус использования приза '{user_prize.prize.name}' обновлен на 'использован'."
                },
                status=200,
            )

        except School.DoesNotExist:
            return Response({"error": "Школа не найдена"}, status=404)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=403)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
