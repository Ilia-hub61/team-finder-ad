from django.core.management.base import BaseCommand
from django.db import transaction

from projects.models import Project
from users.models import User

USERS = [
    (
        "maria@yandex.ru",
        "Мария",
        "Петрова",
        "+79990000001",
        "UX/UI дизайнер, увлекаюсь созданием пользовательских интерфейсов",
    ),
    (
        "alexey@example.com",
        "Алексей",
        "Иванов",
        "+79990000002",
        "Frontend разработчик с опытом работы в React и TypeScript",
    ),
    (
        "dmitry@example.com",
        "Дмитрий",
        "Сидоров",
        "+79990000003",
        "Backend разработчик, специализируюсь на Python и Django",
    ),
    (
        "olga@example.com",
        "Ольга",
        "Васильева",
        "+79990000004",
        "Product-менеджер, ищу команду для запуска стартапа",
    ),
    (
        "milana@example.com",
        "Милана",
        "Павлова",
        "+79990000005",
        "Frontend-разработчик, люблю горы и свою работу",
    ),
]

PROJECTS = [
    (
        "alexey@example.com",
        "Социальная сеть для программистов",
        "Создаём платформу для общения разработчиков, обмена опытом и поиска команды для проектов. Нужны frontend и backend разработчики.",
        "https://github.com/example/dev-social",
        "open",
    ),
    (
        "maria@yandex.ru",
        "Мобильное приложение для фитнеса",
        "Разрабатываем приложение для отслеживания тренировок и питания. Ищем мобильных разработчиков и дизайнера.",
        "",
        "open",
    ),
    (
        "dmitry@example.com",
        "Приложение для здоровья",
        "Создаём платформу для мониторинга здоровья. Нужны frontend и backend разработчики.",
        "",
        "open",
    ),
    (
        "olga@example.com",
        "Приложение для инвестиций",
        "Ищу UX/UI-дизайнера для разработки приложения. В команде уже есть product-менеджер и backend-разработчик.",
        "",
        "open",
    ),
    (
        "milana@example.com",
        "Агрегатор туристических маршрутов",
        "Собираем подборки пеших маршрутов по горам с отзывами и треками.",
        "https://github.com/example/trails",
        "open",
    ),
    (
        "alexey@example.com",
        "Дашборд для pet-проектов",
        "Панель для отслеживания прогресса личных проектов.",
        "",
        "closed",
    ),
    (
        "maria@yandex.ru",
        "Дизайн-система с открытым кодом",
        "Набор компонентов и гайдлайнов для небольших команд.",
        "",
        "open",
    ),
    (
        "dmitry@example.com",
        "Telegram-бот для заметок",
        "Бот на Python для хранения заметок и напоминаний.",
        "https://github.com/example/notes-bot",
        "open",
    ),
    (
        "olga@example.com",
        "Маркетплейс хендмейда",
        "Площадка для мастеров и покупателей авторских изделий.",
        "",
        "open",
    ),
    (
        "milana@example.com",
        "Сервис бронирования коворкингов",
        "Находим и бронируем рабочие места в городе.",
        "",
        "open",
    ),
    (
        "alexey@example.com",
        "Трекер привычек",
        "Простое приложение для отслеживания привычек с напоминаниями.",
        "",
        "open",
    ),
    (
        "maria@yandex.ru",
        "Портфолио-конструктор",
        "Генератор сайтов-портфолио для дизайнеров.",
        "",
        "open",
    ),
    (
        "dmitry@example.com",
        "Агрегатор вакансий для джунов",
        "Собираем стажировки и вакансии для начинающих.",
        "",
        "open",
    ),
    (
        "olga@example.com",
        "Платформа для менторства",
        "Связываем начинающих специалистов с опытными наставниками.",
        "",
        "open",
    ),
]


class Command(BaseCommand):
    help = (
        "Создаёт тестовых пользователей (пароль: password) и проекты. Безопасно запускать повторно."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        users = {}
        for email, name, surname, phone, about in USERS:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"name": name, "surname": surname, "phone": phone, "about": about},
            )
            if created:
                user.set_password("password")
                user.save()
            users[email] = user

        if Project.objects.exists():
            self.stdout.write("Проекты уже есть, пропускаю их создание.")
            return

        for owner_email, name, description, github_url, status in PROJECTS:
            owner = users[owner_email]
            project = Project.objects.create(
                owner=owner,
                name=name,
                description=description,
                github_url=github_url,
                status=status,
            )
            project.participants.add(owner)

        first = Project.objects.get(name="Социальная сеть для программистов")
        first.participants.add(users["maria@yandex.ru"])
        Project.objects.get(name="Мобильное приложение для фитнеса").participants.add(
            users["alexey@example.com"], users["dmitry@example.com"]
        )
        users["maria@yandex.ru"].favorites.add(first)
        users["alexey@example.com"].favorites.add(
            Project.objects.get(name="Мобильное приложение для фитнеса")
        )
        self.stdout.write(self.style.SUCCESS("Тестовые данные созданы (пароль всех: password)"))
