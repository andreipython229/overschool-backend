from rest_framework import routers
from users.api_views import ProfileViewSet, UserViewSet, UserPseudonymViewSet, AccessDistributionView

router = routers.DefaultRouter()
router.register("user", UserViewSet, basename="user")
router.register("profile", ProfileViewSet, basename="profile")
router.register(r'(?P<school_name>\w+)/user_pseudonym', UserPseudonymViewSet, basename="user_pseudonym")
router.register(r'(?P<school_name>\w+)/access-distribution', AccessDistributionView, basename='access-distribution')


urlpatterns = router.urls
