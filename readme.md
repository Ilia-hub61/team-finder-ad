# TeamFinder (вариант 1: «Избранное» и фильтрация пользователей)

Платформа для поиска единомышленников для pet-проектов. Django 5.2 + PostgreSQL.

## Запуск

```bash
python3 -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env_example .env                # TASK_VERSION=1 уже указан; при желании можно поменять значения
docker compose up -d                # PostgreSQL в контейнере, данные лежат в volume postgres_data

python manage.py migrate
python manage.py seed_demo          # тестовые пользователи и проекты (пароль у всех: password)
python manage.py createsuperuser    # администратор (по желанию)
python manage.py runserver
```

Сайт: http://localhost:8000, админ-панель: http://localhost:8000/admin/.

Порт БД берётся из `POSTGRES_PORT` в `.env` (и для `docker-compose.yml`, и для Django).

Тестовые аккаунты после `seed_demo` (пароль `password`): `maria@yandex.ru`,
`alexey@example.com`, `dmitry@example.com`, `olga@example.com`, `milana@example.com`.
У каждого есть проекты, всего 14 (для проверки пагинации), есть участия и избранное.

Тесты и линтер:

```bash
python manage.py test
flake8
```

## Что реализовано

* Приложения `users` (кастомная модель `User` с входом по email, аватарка по умолчанию —
  первая буква имени на однотонном фоне, генерируется Pillow до сохранения в БД) и `projects`.
* Все страницы из задания: главная, вход, регистрация, профиль, редактирование профиля,
  создание/редактирование/страница проекта, список пользователей, смена пароля, выход.
* Вариант 1: `User.favorites` / `Project.interested_users`, `POST /projects/<id>/toggle-favorite/`,
  страница `/projects/favorites/`, фильтры `/users/list/?filter=` —
  `owners-of-favorite-projects`, `owners-of-participating-projects`,
  `interested-in-my-projects`, `participants-of-my-projects` (только для авторизованных).
* Пагинация по 12 элементов на главной и в списке пользователей.
* Админ-панель (`is_staff`): создание, блокировка (`is_active`), удаление аккаунтов,
  смена пароля любого пользователя, редактирование и удаление любых проектов.
* Валидация телефона (`8XXXXXXXXXX` / `+7XXXXXXXXXX`, хранится как `+7…`, уникален независимо
  от формата) и ссылки на GitHub (валидный URL, домен github.com).

* **Телефон** обязателен в описании модели, но в форме регистрации его нет. Поэтому поле
  `phone` может быть пустым; заполняется и проверяется в «Редактировании профиля».
* **Аватар** в форме не обязателен: если файл не загружен, остаётся текущая (сгенерированная).
* **Фильтры пользователей** «Авторы проектов, в которых я участвую» и «Участники моих проектов»
  не показывают самого пользователя (автор всегда участник своего проекта).
* В `project_list.html` кнопка «Создать проект» показывается только авторизованным.
* Автор не может «выйти» из участников своего проекта (эндпоинт отвечает 400).
