from courses.urls import router as courses_router
from rest_framework import routers
from users.urls import router as users_router

router = routers.DefaultRouter()
router.registry += users_router.registry + courses_router.registry
