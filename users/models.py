import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models import Q

from team_finder.validators import validate_github_url

from .managers import UserManager
from .utils import generate_avatar


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        "Email",
        unique=True,
        error_messages={"unique": "Пользователь с таким email уже существует."},
    )
    name = models.CharField("Имя", max_length=124)
    surname = models.CharField("Фамилия", max_length=124)
    avatar = models.ImageField("Аватар", upload_to="avatars/", blank=True)
    phone = models.CharField("Телефон", max_length=12, blank=True)
    github_url = models.URLField("GitHub", blank=True, validators=[validate_github_url])
    about = models.TextField("О себе", max_length=256, blank=True)
    is_active = models.BooleanField("Активен", default=True)
    is_staff = models.BooleanField("Администратор", default=False)
    favorites = models.ManyToManyField(
        "projects.Project",
        related_name="interested_users",
        blank=True,
        verbose_name="Избранные проекты",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    objects = UserManager()

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"
        constraints = [
            models.UniqueConstraint(
                fields=["phone"],
                condition=~Q(phone=""),
                name="unique_non_empty_phone",
            ),
        ]

    def __str__(self):
        return f"{self.name} {self.surname} <{self.email}>"

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        if not self.avatar:
            self.avatar.save(
                f"avatar_{uuid.uuid4()}.png", generate_avatar(self.name), save=False
            )
        super().save(*args, **kwargs)
