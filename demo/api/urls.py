from django.urls import path
from .views import DemoStatusView, start_demo

app_name = "demo"
urlpatterns = [
    path("", start_demo, name="start"),
    path("status/", DemoStatusView.as_view(), name="status"),
]
