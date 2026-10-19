from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import RedirectView, TemplateView


class HomeView(RedirectView):
    url = reverse_lazy("frontend:login")
    permanent = False


@method_decorator(never_cache, name="dispatch")
class RegisterPageView(TemplateView):
    template_name = "frontend/register.html"


@method_decorator(never_cache, name="dispatch")
class LoginPageView(TemplateView):
    template_name = "frontend/login.html"


@method_decorator(never_cache, name="dispatch")
class AccountPageView(TemplateView):
    template_name = "frontend/account.html"


@method_decorator(never_cache, name="dispatch")
class TasksPageView(TemplateView):
    template_name = "frontend/tasks.html"
