from django.urls import path
from rest_framework import routers
from users.api_views import SchoolUserViewSet, RegisterView, LoginView, UserView, LogoutView

router = routers.DefaultRouter()
router.register("users", SchoolUserViewSet, basename="users")

urlpatterns_to_add = [
    path('register', RegisterView.as_view(), name='register'),
    path('login', LoginView.as_view(), name='login'),
    path('user', UserView.as_view(), name='user'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('admin_register/', RegisterView.as_view(), name='register')
]
urlpatterns = router.urls
urlpatterns += urlpatterns_to_add