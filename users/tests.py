from django.test import TestCase
from django.urls import reverse

from projects.models import Project
from team_finder.testing import TempMediaMixin

from .models import User


def make_user(email="a@example.com", name="Анна", surname="Иванова", password="pass12345", **kw):
    return User.objects.create_user(
        email=email, password=password, name=name, surname=surname, **kw
    )


class UserModelTests(TempMediaMixin, TestCase):
    def test_avatar_generated_on_create(self):
        user = make_user()
        self.assertTrue(user.avatar)
        self.assertTrue(user.avatar.name.startswith("avatars/avatar_"))
        self.assertTrue(user.avatar.storage.exists(user.avatar.name))

    def test_email_is_normalized(self):
        self.assertEqual(make_user(email=" A@Example.COM ").email, "a@example.com")


class AuthTests(TempMediaMixin, TestCase):
    def test_register_logs_in_and_redirects_to_list(self):
        resp = self.client.post(
            reverse("users:register"),
            {
                "name": "Иван",
                "surname": "Петров",
                "email": "ivan@example.com",
                "password": "secret123",
            },
        )
        self.assertRedirects(resp, reverse("projects:list"))
        user = User.objects.get(email="ivan@example.com")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
        self.assertTrue(user.check_password("secret123"))

    def test_register_duplicate_email(self):
        make_user()
        resp = self.client.post(
            reverse("users:register"),
            {
                "name": "Иван",
                "surname": "Петров",
                "email": "A@example.com",
                "password": "secret123",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(User.objects.count(), 1)

    def test_login_ok_and_bad(self):
        make_user()
        bad = self.client.post(reverse("users:login"), {"email": "a@example.com", "password": "x"})
        self.assertContains(bad, "Неверный имейл или пароль")
        ok = self.client.post(
            reverse("users:login"), {"email": "a@example.com", "password": "pass12345"}
        )
        self.assertRedirects(ok, reverse("projects:list"))

    def test_logout(self):
        user = make_user()
        self.client.force_login(user)
        self.assertRedirects(self.client.get(reverse("users:logout")), reverse("projects:list"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_change_password(self):
        user = make_user()
        self.client.force_login(user)
        resp = self.client.post(
            reverse("users:change-password"),
            {
                "old_password": "pass12345",
                "new_password1": "newpass789",
                "new_password2": "newpass789",
            },
        )
        self.assertRedirects(resp, reverse("users:detail", args=[user.pk]))
        user.refresh_from_db()
        self.assertTrue(user.check_password("newpass789"))

    def test_anonymous_redirected_from_protected_pages(self):
        for name in (
            "users:edit-profile",
            "users:change-password",
            "projects:create",
            "projects:favorites",
        ):
            self.assertEqual(self.client.get(reverse(name)).status_code, 302, name)


class ProfileTests(TempMediaMixin, TestCase):
    def setUp(self):
        self.user = make_user(phone="+79991112233")
        self.other = make_user(email="b@example.com", phone="+79990000000")
        self.client.force_login(self.user)

    def post(self, **data):
        payload = {"name": "Анна", "surname": "Иванова", "about": "", "phone": "", "github_url": ""}
        payload.update(data)
        return self.client.post(reverse("users:edit-profile"), payload)

    def test_phone_normalised(self):
        self.assertEqual(self.post(phone="89995554433").status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, "+79995554433")

    def test_phone_bad_format(self):
        self.assertEqual(self.post(phone="12345").status_code, 200)

    def test_phone_unique_across_formats(self):
        resp = self.post(phone="89990000000")  # у другого пользователя +79990000000
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "уже существует")

    def test_github_must_be_github(self):
        self.assertEqual(self.post(github_url="https://example.com/x").status_code, 200)
        self.assertEqual(self.post(github_url="not a url").status_code, 200)
        self.assertEqual(self.post(github_url="https://github.com/x").status_code, 302)

    def test_profile_page(self):
        self.assertContains(
            self.client.get(reverse("users:detail", args=[self.user.pk])), "Анна Иванова"
        )


class UserListTests(TempMediaMixin, TestCase):
    def setUp(self):
        self.me = make_user(email="me@example.com", name="Я")
        self.a = make_user(email="a@example.com", name="Автор")
        self.b = make_user(email="b@example.com", name="Бэ")
        self.c = make_user(email="c@example.com", name="Це")
        self.pa = Project.objects.create(owner=self.a, name="PA")
        self.pa.participants.add(self.a, self.me)
        self.pme = Project.objects.create(owner=self.me, name="PM")
        self.pme.participants.add(self.me, self.b)
        self.me.favorites.add(self.pa)
        self.c.favorites.add(self.pme)
        self.client.force_login(self.me)

    def ids(self, flt):
        resp = self.client.get(reverse("users:list"), {"filter": flt})
        return {u.pk for u in resp.context["participants"]}

    def test_sorted_by_id(self):
        resp = self.client.get(reverse("users:list"))
        pks = [u.pk for u in resp.context["participants"]]
        self.assertEqual(pks, sorted(pks))

    def test_filters(self):
        self.assertEqual(self.ids("owners-of-favorite-projects"), {self.a.pk})
        self.assertEqual(self.ids("owners-of-participating-projects"), {self.a.pk})
        self.assertEqual(self.ids("interested-in-my-projects"), {self.c.pk})
        self.assertEqual(self.ids("participants-of-my-projects"), {self.b.pk})

    def test_filter_ignored_for_anonymous(self):
        self.client.logout()
        resp = self.client.get(reverse("users:list"), {"filter": "interested-in-my-projects"})
        self.assertEqual(len(resp.context["participants"]), 4)
        self.assertIsNone(resp.context["active_filter"])

    def test_pagination_12(self):
        for i in range(15):
            make_user(email=f"u{i}@example.com")
        resp = self.client.get(reverse("users:list"))
        self.assertEqual(len(resp.context["participants"]), 12)
