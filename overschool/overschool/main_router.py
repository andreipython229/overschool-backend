from common_services.urls import router as common_services_router
from courses.urls import router as courses_router
from courses.urls import router_appeals as appeals_router
from courses.urls import router_catalog as catalog_router
from courses.urls import router_video as video_router
from rest_framework import routers
from schools.urls import router as schools_router
from schools.urls import router_meetings as meeting_router
from users.urls import router as users_router
from tg_notifications.urls import router as tg_notifications_router

router = routers.DefaultRouter()
router.registry += courses_router.registry + common_services_router.registry + meeting_router.registry

user_router = routers.DefaultRouter()
user_router.registry += users_router.registry

school_router = routers.DefaultRouter()
school_router.registry += schools_router.registry

videos_router = routers.DefaultRouter()
videos_router.registry += video_router.registry

catalogs_router = routers.DefaultRouter()
catalogs_router.registry += catalog_router.registry

appeal_router = routers.DefaultRouter()
appeal_router.registry += appeals_router.registry

notifications_router = routers.DefaultRouter()
notifications_router.registry += tg_notifications_router.registry
