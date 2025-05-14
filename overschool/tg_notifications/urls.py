from django.urls import path
from rest_framework import routers

from .api_views import (NotificationsViewSet,
                        SendMessageViewSet,
                        MeetingReminderViewSet
                        )

router = routers.DefaultRouter()

router.register("tg_notif", NotificationsViewSet, basename="tg_notif")
router.register(r'tg_messages', SendMessageViewSet, basename="tg_messages")
router.register(r'reminders', MeetingReminderViewSet, basename="reminders")

urlpatterns = router.urls
