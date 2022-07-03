from rest_framework.routers import SimpleRouter
from .views import MainCourseModelView

router = SimpleRouter()
router.register('video', MainCourseModelView, basename="video")

urlpatterns = router.urls