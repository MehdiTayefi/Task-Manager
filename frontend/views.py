from django.views.generic import RedirectView, TemplateView
from django.urls import reverse_lazy


class HomeView(RedirectView):
    url = reverse_lazy("frontend:register")
    permanent = False


class RegisterPageView(TemplateView):
    template_name = "frontend/register.html"