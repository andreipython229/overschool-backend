from datetime import timedelta

import requests
from common_services.mixins import WithHeadersViewSet
from common_services.selectel_client import UploadToS3
from django.utils.timezone import now
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from schools.models import Box, BoxPrize, Payment, Prize, School, SchoolPaymentMethod
from schools.school_mixin import SchoolMixin
from schools.serializers import (
    BoxDetailSerializer,
    BoxPrizeSerializer,
    BoxSerializer,
    PaymentSerializer,
    PrizeDetailSerializer,
    PrizeSerializer,
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
        self.request.user
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
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
        school_name = self.kwargs.get("school_name")
        school_id = School.objects.get(name=school_name).school_id
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


class CreatePaymentLinkView(WithHeadersViewSet, SchoolMixin, APIView):
    """
    Эндпоинт для создания ссылки на оплату коробки.
    """

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
            payload = {
                "Token": token,
                "AccountNo": payment.id,
                "Amount": payment.amount,
                "Currency": 933,
                "Info": f"Оплата {box.name}",
                "ReturnInvoiceUrl": 1,
                # "ReturnUrl": "https://platform.coursehb.ru",
                # "FailUrl": "https://platform.coursehb.ru",
            }

            response = requests.post(api_url, data=payload)
            if response.status_code != 200:
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


class CheckPaymentStatusView(WithHeadersViewSet, SchoolMixin, APIView):
    """
    Эндпоинт для проверки статусов платежей, ожидающих оплаты.
    """

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
                print(response.json())
                print(response.status_code)

                if response.status_code == 200:
                    status_code = response.json().get("Status")

                    # Обновляем статус платежа на основании кода статуса
                    if status_code == 3 or status_code == 6:  # Успешно оплачено
                        payment.payment_status = "completed"
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
