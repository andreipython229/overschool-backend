from rest_framework import viewsets
from .models import Feedback, Tariff
from .serializers import FeedbackSerializer, TariffSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, JSONParser]
    lookup_field = 'pk'

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TariffViewSet(viewsets.ModelViewSet):
    queryset = Tariff.objects.filter(is_active=True)
    serializer_class = TariffSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def list(self, request, *args, **kwargs):
        """
        Получить список всех активных тарифов.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """
        Сохранить новый тариф.
        """
        serializer.save()


class TariffSchoolOwner(viewsets.ViewSet):
    def list(self, request):
        """
        Получить текущий тариф для школы.
        """
        # Логика для получения текущего тарифа школы
        # Например, можно использовать school_name из запроса
        school_name = request.query_params.get('school_name')
        if not school_name:
            return Response({"detail": "School name is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Здесь должна быть логика для получения тарифа
        # Например, можно использовать Tariff.objects.filter(school_name=school_name)
        # и вернуть текущий тариф
        return Response({"detail": "Тариф успешно получен."}, status=status.HTTP_200_OK)


class SignupSchoolOwnerView(APIView):
    """
    View для регистрации владельца школы
    """
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request):
        print("=== DEBUG: SignupSchoolOwnerView.post() ===")
        print(f"Request data: {request.data}")
        print(f"Request method: {request.method}")
        print(f"Content type: {request.content_type}")

        try:
            # Получаем данные из запроса
            data = request.data

            # Проверяем наличие обязательных полей
            required_fields = ['school_name', 'email', 'phone_number', 'password', 'tariff']
            for field in required_fields:
                if not data.get(field):
                    print(f"Missing required field: {field}")
                    return Response(
                        {'error': f'Поле {field} обязательно для заполнения'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            print(f"Looking for tariff: {data['tariff']}")

            # Проверяем, что тариф существует
            try:
                tariff = Tariff.objects.get(name=data['tariff'], is_active=True)
                print(f"Found tariff: {tariff.name} with price: {tariff.price}")
            except Tariff.DoesNotExist:
                print(f"Tariff not found: {data['tariff']}")
                # Проверим, какие тарифы есть в базе
                all_tariffs = Tariff.objects.all().values('name', 'price', 'is_active')
                print(f"Available tariffs: {list(all_tariffs)}")
                return Response(
                    {'error': f'Тариф {data["tariff"]} не найден или неактивен'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Проверяем, что email не занят
            if User.objects.filter(email=data['email']).exists():
                print(f"Email already exists: {data['email']}")
                return Response(
                    {'error': 'Пользователь с таким email уже существует'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Проверяем, что название школы не занято
            if User.objects.filter(username=data['school_name']).exists():
                print(f"School name already exists: {data['school_name']}")
                return Response(
                    {'error': 'Пользователь с таким названием школы уже существует'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Создаем пользователя
            with transaction.atomic():
                user = User.objects.create_user(
                    username=data['school_name'],
                    email=data['email'],
                    password=data['password'],
                    first_name=data.get('first_name', ''),
                    last_name=data.get('last_name', '')
                )

                # Обновляем телефон отдельно
                user.phone = data.get('phone_number', '')
                user.save()

                print(f"User created successfully: {user.username}")

                # Здесь можно добавить логику создания школы
                # и привязки к тарифу

            return Response({
                'message': 'Регистрация успешна',
                'user_id': user.id,
                'school_name': user.username,
                'tariff': tariff.name
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"Exception occurred: {str(e)}")
            return Response({
                'error': f'Ошибка при регистрации: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)