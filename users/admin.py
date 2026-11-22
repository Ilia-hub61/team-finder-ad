from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.password_validation import validate_password

from .models import User


class AdminUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Подтверждение пароля", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("email", "name", "surname", "phone")

    def clean_password2(self):
        p1, p2 = self.cleaned_data.get("password1"), self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Пароли не совпадают")
        if p2:
            validate_password(p2)
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = AdminUserCreationForm
    ordering = ("-id",)
    list_display = ("email", "name", "surname", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("email", "name", "surname")
    filter_horizontal = ("groups", "user_permissions", "favorites")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Профиль", {"fields": ("name", "surname", "avatar", "phone", "github_url", "about")}),
        ("Избранное", {"fields": ("favorites",)}),
        (
            "Права",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "name", "surname", "phone", "password1", "password2"),
            },
        ),
    )
