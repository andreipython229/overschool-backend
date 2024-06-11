from django.urls import path
from rest_framework import routers

from .views import NotificationsViewSet, SendMessageViewSet

router = routers.DefaultRouter()

router.register("tg_notif", NotificationsViewSet, basename="tg_notif")
# router.register(r'reminders', MeetingsRemindersViewSet)
router.register(r'tg_messages', SendMessageViewSet, basename="tg_messages")

urlpatterns = router.urls
