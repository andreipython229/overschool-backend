from courses.api_views import (
    AnswerViewSet,
    CourseViewSet,
    HomeworkCheckViewSet,
    HomeworkStatisticsView,
    HomeworkViewSet,
    LessonAvailabilityViewSet,
    LessonViewSet,
    QuestionViewSet,
    SectionViewSet,
    StudentProgressViewSet,
    StudentsGroupSettingsViewSet,
    StudentsGroupViewSet,
    StudentsGroupWithoutTeacherViewSet,
    StudentsTableInfoViewSet,
    TestViewSet,
    UserHomeworkViewSet,
    UserTestViewSet,
)
from rest_framework import routers

router = routers.DefaultRouter()
router.register("courses", CourseViewSet, basename="courses")
router.register("sections", SectionViewSet, basename="sections")
router.register("lessons", LessonViewSet, basename="lessons")
router.register("students_group", StudentsGroupViewSet, basename="students_group")
router.register(
    "students_group_no_teacher",
    StudentsGroupWithoutTeacherViewSet,
    basename="students_group_no_teacher",
)
router.register(
    "students_group_settings",
    StudentsGroupSettingsViewSet,
    basename="students_group_settings",
)
router.register(
    "students_table_info", StudentsTableInfoViewSet, basename="students_table_info"
)
router.register(
    "lesson-availability", LessonAvailabilityViewSet, basename="lesson-availability"
)
router.register("homeworks", HomeworkViewSet, basename="homeworks")
router.register("homeworks_stats", HomeworkStatisticsView, basename="homeworks_stats")
router.register(
    "user_homework_checks", HomeworkCheckViewSet, basename="user_homework_checks"
)

router.register("user_homeworks", UserHomeworkViewSet, basename="user_homeworks")
router.register("tests", TestViewSet, basename="tests")
router.register("questions", QuestionViewSet, basename="questions")
router.register("answers", AnswerViewSet, basename="answers")
router.register("usertest", UserTestViewSet, basename="test_user")
router.register("student_progress", StudentProgressViewSet, basename="student_progress")

urlpatterns = router.urls
