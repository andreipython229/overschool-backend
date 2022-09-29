from rest_framework import routers

from courses.api_views import (
    CourseViewSet,
    CourseDataSet,
    AudioFileView,
    LessonViewSet,
    SectionViewSet,
    StudentsGroupViewSet,
    SchoolHeaderViewSet,
    StudentsTableInfoViewSet,
    UsersCourse,
    GroupUsersByMonthView,
    CourseUsersByMonthView,
    UsersGroup
)

router = routers.DefaultRouter()
router.register("school_header", SchoolHeaderViewSet, basename="school_header")
router.register("courses", CourseViewSet, basename="courses")
router.register("sections", SectionViewSet, basename="sections")
router.register("lessons", LessonViewSet, basename="lessons")
router.register("audiofile", AudioFileView, basename="audiofile")
router.register("students_group", StudentsGroupViewSet, basename="students_group")
router.register("course_stat", UsersCourse, basename="course_stat")
router.register("user_count_by_month_group", GroupUsersByMonthView, basename="user_count_by_month_group")
router.register("user_count_by_month_course", CourseUsersByMonthView, basename="user_count_by_month_course")
router.register("group_stat", UsersGroup, basename="group_stat")
router.register("courses_data", CourseDataSet, basename="courses_data")
router.register("students_table_info", StudentsTableInfoViewSet, basename="students_table_info")

urlpatterns = router.urls
