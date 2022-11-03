from rest_framework import routers

from courses.api_views import (AnswerViewSet, CourseViewSet,
                               HomeworkStatisticsView, HomeworkViewSet,
                               LessonViewSet, QuestionViewSet, SectionViewSet,
                               StudentsGroupViewSet, StudentsTableInfoViewSet,
                               TeacherHomeworkViewSet, TestViewSet,
                               UserHomeworkViewSet, UserTestViewSet,UserHistoryViewSet)

router = routers.DefaultRouter()
router.register("courses", CourseViewSet, basename="courses")
router.register("sections", SectionViewSet, basename="sections")
router.register("lessons", LessonViewSet, basename="lessons")
router.register("students_group", StudentsGroupViewSet, basename="students_group")
router.register(
    "students_table_info", StudentsTableInfoViewSet, basename="students_table_info"
)
router.register("homeworks", HomeworkViewSet, basename="homeworks")
router.register("homeworks_stats", HomeworkStatisticsView, basename="homeworks_stats")
router.register("user_history", UserHistoryViewSet, basename="user_history")
router.register("user_homeworks", UserHomeworkViewSet, basename="user_homeworks")
router.register(
    "teacher_homeworks", TeacherHomeworkViewSet, basename="teacher_homeworks"
)
router.register("tests", TestViewSet, basename="tests")
router.register("questions", QuestionViewSet, basename="questions")
router.register("answers", AnswerViewSet, basename="answers")
router.register("usertest", UserTestViewSet, basename="test_user")

urlpatterns = router.urls
