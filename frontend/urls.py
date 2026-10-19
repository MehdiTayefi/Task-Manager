from django.urls import path

from .views import HomeView, RegisterPageView

app_name = "frontend"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("register/", RegisterPageView.as_view(), name="register"),
]
