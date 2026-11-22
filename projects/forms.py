from django import forms

from .models import Project


class ProjectForm(forms.ModelForm):
    status = forms.ChoiceField(
        label="Статус",
        choices=[(Project.Status.OPEN, "Открытый"), (Project.Status.CLOSED, "Закрытый")],
    )

    class Meta:
        model = Project
        fields = ["name", "description", "github_url", "status"]
        labels = {
            "name": "Название проекта",
            "description": "Описание проекта",
            "github_url": "Ссылка на GitHub репозиторий",
        }
        widgets = {
            "description": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Опишите ваш проект..."}
            ),
            "github_url": forms.URLInput(
                attrs={"placeholder": "https://github.com/username/repository"}
            ),
        }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
