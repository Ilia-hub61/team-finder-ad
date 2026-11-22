import re

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

from .models import User

PHONE_RE = re.compile(r"(?:\+7|8)\d{10}")


class NoSuffixMixin:
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)


class RegisterForm(NoSuffixMixin, forms.ModelForm):
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["name", "surname", "email", "password"]

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(NoSuffixMixin, forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user = None

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        password = cleaned.get("password")
        if email and password:
            self.user = authenticate(self.request, email=email.strip().lower(), password=password)
            if self.user is None:
                raise forms.ValidationError("Неверный имейл или пароль")
        return cleaned


class ProfileForm(NoSuffixMixin, forms.ModelForm):
    phone = forms.CharField(label="Телефон", required=False, max_length=20)

    class Meta:
        model = User
        fields = ["name", "surname", "avatar", "about", "phone", "github_url"]
        widgets = {
            "avatar": forms.FileInput(attrs={"accept": "image/*"}),
            "about": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["avatar"].required = False

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if not phone:
            return ""
        if not PHONE_RE.fullmatch(phone):
            raise forms.ValidationError(
                "Телефон должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX"
            )
        digits = phone[-10:]
        busy = User.objects.filter(phone__in=[f"+7{digits}", f"8{digits}"])
        if busy.exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Пользователь с таким телефоном уже существует")
        return f"+7{digits}"
