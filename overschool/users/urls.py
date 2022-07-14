from django.urls import path
from rest_framework import routers
from users.api_views import SchoolUserViewSet, RegisterView

router = routers.DefaultRouter()
router.register("users", SchoolUserViewSet, basename="users")

# urlpatterns = [
#     path('register', RegisterView.as_view(), name='register')
# ]
urlpatterns = router.urls
urlpatterns.append(path('register', RegisterView.as_view(), name='register'))