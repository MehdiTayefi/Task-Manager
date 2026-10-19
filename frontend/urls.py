from django.urls import path

from . import auth_views
from .views import AccountPageView, HomeView, LoginPageView, RegisterPageView, TasksPageView

app_name = "frontend"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("register/", RegisterPageView.as_view(), name="register"),
    path("login/", LoginPageView.as_view(), name="login"),
    path("tasks/", TasksPageView.as_view(), name="tasks"),
    path("account/", AccountPageView.as_view(), name="account"),
    path("browser-auth/login/", auth_views.browser_login, name="browser-login"),
    path("browser-auth/refresh/", auth_views.browser_refresh, name="browser-refresh"),
    path("browser-auth/logout/", auth_views.browser_logout, name="browser-logout"),
]
