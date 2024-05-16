from courses.api_views import (
    AnswerViewSet,
    BaseLessonBlockViewSet,
    BlockButtonViewSet,
    CommentViewSet,
    CourseCatalogViewSet,
    CourseViewSet,
    GetAppealsViewSet,
    GroupCourseAccessViewSet,
    HomeworkCheckViewSet,
    HomeworkStatisticsView,
    HomeworkViewSet,
    LessonAvailabilityViewSet,
    LessonEnrollmentViewSet,
    LessonViewSet,
    QuestionViewSet,
    SectionViewSet,
    StudentProgressViewSet,
    StudentsGroupSettingsViewSet,
    StudentsGroupViewSet,
    StudentsGroupWithoutTeacherViewSet,
    StudentsTableInfoViewSet,
    TestViewSet,
    UploadVideoViewSet,
    UserHomeworkViewSet,
    UserTestViewSet,
)
from django.urls import path
from rest_framework import routers
from schools.api_views import SchoolDocumentViewSet

router = routers.DefaultRouter()
router.register("courses", CourseViewSet, basename="courses")
router.register("school_document", SchoolDocumentViewSet, basename="school_document")
router.register("sections", SectionViewSet, basename="sections")
router.register("lessons", LessonViewSet, basename="lessons")
router.register("blocks", BaseLessonBlockViewSet, basename="blocks")
router.register("block_buttons", BlockButtonViewSet, basename="block_buttons")
router.register("students_group", StudentsGroupViewSet, basename="students_group")
router.register(
    "group_course_access", GroupCourseAccessViewSet, basename="group_course_access"
)
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
router.register(
    "lesson-enrollment", LessonEnrollmentViewSet, basename="lesson-enrollment"
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
router.register("lesson_comments", CommentViewSet, basename="lesson_comments")

urlpatterns = router.urls

router_video = routers.DefaultRouter()

router_video.register("block_video", UploadVideoViewSet, basename="block_video")

router_catalog = routers.DefaultRouter()

router_catalog.register(
    "course_catalog", CourseCatalogViewSet, basename="course_catalog"
)

router_appeals = routers.DefaultRouter()

router_appeals.register("course-appeals", GetAppealsViewSet, basename="course-appeals")
