from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from team_finder.utils import paginate

from .forms import ProjectForm
from .models import Project

User = get_user_model()


def _with_favorites(request):
    if request.user.is_authenticated:
        request.user = User.objects.prefetch_related("favorites").get(
            pk=request.user.pk
        )


def _base_queryset():
    return Project.objects.select_related("owner").prefetch_related("participants")


def project_list(request):
    _with_favorites(request)
    page_obj = paginate(request, _base_queryset())
    return render(
        request,
        "projects/project_list.html",
        {"projects": page_obj, "page_obj": page_obj, "query_prefix": ""},
    )


@login_required
def favorite_projects(request):
    _with_favorites(request)
    projects = _base_queryset().filter(interested_users=request.user)
    return render(request, "projects/favorite_projects.html", {"projects": projects})


def project_detail(request, project_id):
    _with_favorites(request)
    project = get_object_or_404(_base_queryset(), pk=project_id)
    return render(request, "projects/project-details.html", {"project": project})


def _project_form(request, project=None):
    is_edit = project is not None
    form = ProjectForm(request.POST or None, instance=project)
    if request.method == "POST" and form.is_valid():
        project = form.save(commit=False)
        if not is_edit:
            project.owner = request.user
        project.save()
        if not is_edit:
            project.participants.add(request.user)
        return redirect("projects:detail", project_id=project.pk)
    return render(
        request, "projects/create-project.html", {"form": form, "is_edit": is_edit}
    )


@login_required
def create_project(request):
    return _project_form(request)


@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner_id != request.user.pk:
        raise PermissionDenied
    return _project_form(request, project)


def _error(message, status):
    return JsonResponse({"status": "error", "message": message}, status=status)


@require_POST
def toggle_favorite(request, project_id):
    if not request.user.is_authenticated:
        return _error("Требуется авторизация", 401)
    project = get_object_or_404(Project, pk=project_id)
    favorites = request.user.favorites
    if favorites.filter(pk=project.pk).exists():
        favorites.remove(project)
        favorited = False
    else:
        favorites.add(project)
        favorited = True
    return JsonResponse({"status": "ok", "favorited": favorited})


@require_POST
def complete_project(request, project_id):
    if not request.user.is_authenticated:
        return _error("Требуется авторизация", 401)
    project = get_object_or_404(Project, pk=project_id)
    if project.owner_id != request.user.pk:
        return _error("Только автор может завершить проект", 403)
    if project.status != Project.Status.OPEN:
        return _error("Проект уже завершён", 400)
    project.status = Project.Status.CLOSED
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok", "project_status": project.status})


@require_POST
def toggle_participate(request, project_id):
    if not request.user.is_authenticated:
        return _error("Требуется авторизация", 401)
    project = get_object_or_404(Project, pk=project_id)
    if project.owner_id == request.user.pk:
        return _error("Автор всегда участвует в своём проекте", 400)
    if project.participants.filter(pk=request.user.pk).exists():
        project.participants.remove(request.user)
        participant = False
    else:
        project.participants.add(request.user)
        participant = True
    return JsonResponse({"status": "ok", "participant": participant})
