from django.urls import path
from rest_framework import routers

from .views import NotificationsViewSet

router = routers.DefaultRouter()

router.register("tg_notif", NotificationsViewSet, basename="tg_notif")

urlpatterns = router.urls
