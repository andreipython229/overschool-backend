from rest_framework.routers import SimpleRouter
from .views import MainCourseModelView

router = SimpleRouter()
router.register('course', MainCourseModelView, basename="course")

urlpatterns = router.urls