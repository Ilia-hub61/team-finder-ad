import team_finder.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200, verbose_name="Название")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, db_index=True, verbose_name="Дата создания"
                    ),
                ),
                (
                    "github_url",
                    models.URLField(
                        blank=True,
                        validators=[team_finder.validators.validate_github_url],
                        verbose_name="Ссылка на GitHub",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("open", "Open"), ("closed", "Closed")],
                        default="open",
                        max_length=6,
                        verbose_name="Статус",
                    ),
                ),
            ],
            options={
                "verbose_name": "проект",
                "verbose_name_plural": "проекты",
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]
