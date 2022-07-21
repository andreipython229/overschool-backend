

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("user.urls")),
    path(r"", include(("fileupload.urls", "fileupload"), namespace="api")),
]
