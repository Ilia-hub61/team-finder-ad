import json

from django.test import TestCase
from django.urls import reverse

from team_finder.testing import TempMediaMixin
from users.models import User

from .models import Project


def make_user(email, name="Имя"):
    return User.objects.create_user(email=email, password="pass12345", name=name, surname="Фам")


class ProjectTests(TempMediaMixin, TestCase):
    def setUp(self):
        self.owner = make_user("owner@example.com")
        self.user = make_user("user@example.com")
        self.project = Project.objects.create(owner=self.owner, name="P")
        self.project.participants.add(self.owner)

    def post_json(self, name, project=None):
        return self.client.post(
            reverse(name, args=[(project or self.project).pk]),
            data="{}",
            content_type="application/json",
        )

    def test_root_redirects_to_list(self):
        self.assertRedirects(self.client.get("/"), "/projects/list/", target_status_code=200)

    def test_list_sorted_and_paginated(self):
        for i in range(14):
            Project.objects.create(owner=self.owner, name=f"N{i}")
        resp = self.client.get(reverse("projects:list"))
        self.assertEqual(len(resp.context["projects"]), 12)
        names = [p.name for p in resp.context["projects"]]
        self.assertEqual(names[0], "N13")
        self.assertEqual(
            len(self.client.get(reverse("projects:list"), {"page": 2}).context["projects"]), 3
        )

    def test_guest_sees_no_create_or_favorite_controls(self):
        resp = self.client.get(reverse("projects:list"))
        self.assertNotContains(resp, "project-fav-icon\n")
        self.assertNotContains(resp, "+ Создать проект")

    def test_create_sets_owner_and_participant(self):
        self.client.force_login(self.user)
        resp = self.client.post(
            reverse("projects:create"),
            {
                "name": "Новый",
                "description": "d",
                "github_url": "https://github.com/a/b",
                "status": "open",
            },
        )
        project = Project.objects.get(name="Новый")
        self.assertRedirects(resp, reverse("projects:detail", args=[project.pk]))
        self.assertEqual(project.owner, self.user)
        self.assertIn(self.user, project.participants.all())

    def test_create_validation(self):
        self.client.force_login(self.user)
        resp = self.client.post(reverse("projects:create"), {"name": "", "status": "open"})
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(
            reverse("projects:create"),
            {"name": "x", "github_url": "https://gitlab.com/a", "status": "open"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Project.objects.filter(name="x").exists())

    def test_edit_only_owner(self):
        url = reverse("projects:edit", args=[self.project.pk])
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.owner)
        resp = self.client.get(url)
        self.assertTrue(resp.context["is_edit"])
        self.assertEqual(resp.context["form"].initial["name"], "P")
        resp = self.client.post(
            url, {"name": "P2", "description": "", "github_url": "", "status": "closed"}
        )
        self.assertRedirects(resp, reverse("projects:detail", args=[self.project.pk]))
        self.project.refresh_from_db()
        self.assertEqual((self.project.name, self.project.status), ("P2", "closed"))

    def test_toggle_favorite(self):
        self.assertEqual(self.post_json("projects:toggle-favorite").status_code, 401)
        self.client.force_login(self.user)
        r1 = json.loads(self.post_json("projects:toggle-favorite").content)
        self.assertEqual(r1, {"status": "ok", "favorited": True})
        self.assertIn(self.project, self.user.favorites.all())
        r2 = json.loads(self.post_json("projects:toggle-favorite").content)
        self.assertFalse(r2["favorited"])
        self.assertEqual(
            self.client.get(
                reverse("projects:toggle-favorite", args=[self.project.pk])
            ).status_code,
            405,
        )

    def test_favorites_page(self):
        self.user.favorites.add(self.project)
        self.client.force_login(self.user)
        resp = self.client.get(reverse("projects:favorites"))
        self.assertEqual(list(resp.context["projects"]), [self.project])
        other = make_user("o2@example.com")
        self.client.force_login(other)
        self.assertEqual(
            list(self.client.get(reverse("projects:favorites")).context["projects"]), []
        )

    def test_complete(self):
        self.assertEqual(self.post_json("projects:complete").status_code, 401)
        self.client.force_login(self.user)
        self.assertEqual(self.post_json("projects:complete").status_code, 403)
        self.client.force_login(self.owner)
        resp = self.post_json("projects:complete")
        self.assertEqual(json.loads(resp.content), {"status": "ok", "project_status": "closed"})
        self.assertEqual(self.post_json("projects:complete").status_code, 400)

    def test_toggle_participate(self):
        self.assertEqual(self.post_json("projects:toggle-participate").status_code, 401)
        self.client.force_login(self.user)
        self.assertTrue(
            json.loads(self.post_json("projects:toggle-participate").content)["participant"]
        )
        self.assertIn(self.user, self.project.participants.all())
        self.assertFalse(
            json.loads(self.post_json("projects:toggle-participate").content)["participant"]
        )
        self.client.force_login(self.owner)
        self.assertEqual(self.post_json("projects:toggle-participate").status_code, 400)

    def test_detail_shows_owner_controls(self):
        url = reverse("projects:detail", args=[self.project.pk])
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(url), "Завершить проект")
        self.client.force_login(self.user)
        resp = self.client.get(url)
        self.assertContains(resp, "Участвовать")
        self.assertNotContains(resp, "Завершить проект")
