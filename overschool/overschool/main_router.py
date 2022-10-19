from courses.urls import router as courses_router
from homeworks.urls import router as homeworks_router
from lesson_tests.urls import router as lesson_tests_router
from schools.urls import router as schools_router
from rest_framework import routers
from users.urls import router as users_router

router = routers.DefaultRouter()
router.registry += (
        users_router.registry + courses_router.registry + homeworks_router.registry + lesson_tests_router.registry
        + schools_router.registry
)