from rest_framework import routers
from users.views_api import FeedbackViewSet, TariffViewSet

user_router = routers.DefaultRouter()
user_router.register('feedbacks', FeedbackViewSet, basename='feedback')
user_router.register('tariffs', TariffViewSet, basename='tariff')  # Добавляем маршрут для тарифов

urlpatterns = user_router.urls