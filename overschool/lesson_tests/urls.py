from rest_framework import routers

from lesson_tests.api_views import AnswerViewSet, QuestionViewSet, TestViewSet, UserTestViewSet

router = routers.DefaultRouter()
router.register("tests", TestViewSet, basename="tests")
router.register("questions", QuestionViewSet, basename="questions")
router.register("answers", AnswerViewSet, basename="answers")
router.register("usertest", UserTestViewSet, basename="test_user")

urlpatterns = router.urls
