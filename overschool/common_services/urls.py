from common_services.api_views import AudioFileViewSet, TextFileViewSet
from rest_framework import routers

router = routers.DefaultRouter()
router.register("audio_files", AudioFileViewSet, basename="audio_files")
router.register("text_files", TextFileViewSet, basename="text_files")

urlpatterns = router.urls
