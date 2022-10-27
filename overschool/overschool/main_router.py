from rest_framework import routers

from courses.urls import router as courses_router
from users.urls import router as users_router
from schools.urls import router as schools_router
from common_services.urls import router as common_services_router

router = routers.DefaultRouter()
router.registry += users_router.registry + courses_router.registry + schools_router.registry + common_services_router.registry
