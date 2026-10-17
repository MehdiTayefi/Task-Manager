from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form= CustomUserChangeForm
    add_form= CustomUserCreationForm
    change_password_form= AdminPasswordChangeForm

    list_display= (
        "id",
        "username",
        "email",
        "is_active",
        "is_staff",
    )

    search_fields= ("username", "email")
    ordering = ("-id", )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Contact information",{
            "fields": ("email", )
        })
    )

admin.site.unregister(Group)

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass

