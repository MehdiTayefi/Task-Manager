from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/v1/auth/", include("accounts.api.urls")),
    path("api/v1/users/", include("accounts.api.users_urls")),
    path("api/v1/", include("tasks.api.urls")),
    path("", include("frontend.urls")),
    path("browser-auth/demo/", include("demo.api.urls"))
]
