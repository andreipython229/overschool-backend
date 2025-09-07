from rest_framework import routers

from common_services.urls import router as common_services_router
from courses.urls import (
    router as courses_router,
    router_appeals,
    router_catalog,
    router_video,
)
from schools.urls import (
    router as schools_router,
    router_box,
    router_domain,
    router_meetings,
)
from tg_notifications.urls import router as tg_notifications_router
from users.urls import user_router as users_router

# Основной роутер для school_name
school_name_router = routers.DefaultRouter()
school_name_router.registry.extend(courses_router.registry)
school_name_router.registry.extend(common_services_router.registry)
school_name_router.registry.extend(router_meetings.registry)
school_name_router.registry.extend(router_domain.registry)
school_name_router.registry.extend(router_box.registry)

# Отдельные роутеры по смыслу
user_router = routers.DefaultRouter()
user_router.registry.extend(users_router.registry)

school_router = routers.DefaultRouter()
school_router.registry.extend(schools_router.registry)

videos_router = routers.DefaultRouter()
videos_router.registry.extend(router_video.registry)

catalogs_router = routers.DefaultRouter()
catalogs_router.registry.extend(router_catalog.registry)

appeal_router = routers.DefaultRouter()
appeal_router.registry.extend(router_appeals.registry)

notifications_router = routers.DefaultRouter()
notifications_router.registry.extend(tg_notifications_router.registry)