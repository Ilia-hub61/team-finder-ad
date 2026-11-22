from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from team_finder.utils import paginate

from .forms import LoginForm, ProfileForm, RegisterForm
from .models import User

USER_FILTERS = {
    "owners-of-favorite-projects": lambda users, me: users.filter(
        owned_projects__interested_users=me
    ),
    "owners-of-participating-projects": lambda users, me: users.filter(
        owned_projects__participants=me
    ).exclude(pk=me.pk),
    "interested-in-my-projects": lambda users, me: users.filter(favorites__owner=me),
    "participants-of-my-projects": lambda users, me: users.filter(
        participated_projects__owner=me
    ).exclude(pk=me.pk),
}


def register(request):
    if request.user.is_authenticated:
        return redirect("projects:list")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("projects:list")
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("projects:list")
    form = LoginForm(request.POST or None, request=request)
    if request.method == "POST" and form.is_valid():
        login(request, form.user)
        target = request.GET.get("next", "")
        if target and url_has_allowed_host_and_scheme(target, {request.get_host()}):
            return redirect(target)
        return redirect("projects:list")
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("projects:list")


def user_list(request):
    users = User.objects.order_by("id")
    active_filter = None
    if request.user.is_authenticated:
        key = request.GET.get("filter")
        if key in USER_FILTERS:
            users = USER_FILTERS[key](users, request.user).distinct()
            active_filter = key
    page_obj = paginate(request, users)
    return render(
        request,
        "users/participants.html",
        {
            "participants": page_obj,
            "page_obj": page_obj,
            "active_filter": active_filter,
            "query_prefix": f"filter={active_filter}&" if active_filter else "",
        },
    )


def user_detail(request, user_id):
    profile_user = get_object_or_404(User, pk=user_id)
    return render(request, "users/user-details.html", {"user": profile_user})


@login_required
def edit_profile(request):
    form = ProfileForm(
        request.POST or None, request.FILES or None, instance=request.user
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("users:detail", user_id=request.user.pk)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def change_password(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        return redirect("users:detail", user_id=user.pk)
    return render(request, "users/change_password.html", {"form": form})
