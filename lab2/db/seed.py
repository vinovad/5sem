"""Тестовые данные. Заполняют БД только при первом запуске."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from db.database import Database
from db.security import hash_password


def _id() -> str:
    return str(uuid.uuid4())


def _now(delta_days: int = 0, delta_hours: int = 0) -> str:
    moment = datetime.now() + timedelta(days=delta_days, hours=delta_hours)
    return moment.isoformat(timespec="seconds")


def seed_if_empty(db: Database) -> None:
    """Добавляет тестовые данные, если в БД нет пользователей."""
    if not db.is_empty():
        return

    student_id, teacher_id, admin_id = _seed_users(db)
    courses = _seed_courses(db, teacher_id)
    first_course = courses[0]

    # Студент уже записан на первый курс, на остальные может записаться сам
    db.execute(
        "INSERT INTO enrollments (student_id, course_id, enrolled_date) VALUES (?, ?, ?)",
        (student_id, first_course["id"], _now(-7)),
    )
    db.execute(
        "INSERT INTO progress (id, user_id, course_id, lesson_id, status, score, "
        "started_date, completed_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (_id(), student_id, first_course["id"], first_course["first_lesson_id"],
         "completed", 90, _now(-6), _now(-6, 1)),
    )
    db.execute(
        "INSERT INTO reviews (id, user_id, course_id, rating, text, created_date, "
        "is_approved) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (_id(), student_id, first_course["id"], 5,
         "Понятные объяснения и хорошие задания.", _now(-2), 1),
    )
    db.execute(
        "INSERT INTO webinars (id, course_id, title, scheduled_date, duration_minutes, "
        "recording_url, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (_id(), first_course["id"], "Разбор первых заданий по Python",
         _now(1), 60, None, "scheduled"),
    )


def _seed_users(db: Database) -> tuple[str, str, str]:
    student_id, teacher_id, admin_id = _id(), _id(), _id()
    password = hash_password("1234")

    users = [
        (student_id, "student@gmail.com", password, "Иван Петров", "student@gmail.com", "student"),
        (teacher_id, "prepod@gmail.com", password, "Анна Сидорова", "prepod@gmail.com", "teacher"),
        (admin_id, "admin@gmail.com", password, "Олег Иванов", "admin@gmail.com", "admin"),
    ]
    for user in users:
        db.execute(
            "INSERT INTO users (id, username, password_hash, full_name, email, role) "
            "VALUES (?, ?, ?, ?, ?, ?)", user)

    db.execute("INSERT INTO students (user_id, student_group, level) VALUES (?, ?, ?)",
               (student_id, "421702", "beginner"))
    db.execute("INSERT INTO teachers (user_id, specialization, rating) VALUES (?, ?, ?)",
               (teacher_id, "Программирование", 4.8))
    db.execute("INSERT INTO admins (user_id, access_level) VALUES (?, ?)",
               (admin_id, 2))
    return student_id, teacher_id, admin_id


def _seed_courses(db: Database, teacher_id: str) -> list[dict]:
    catalog = [
        {
            "title": "Python для начинающих",
            "description": "Базовый курс: переменные, циклы, функции и работа с файлами.",
            "level": "beginner", "price": 0,
            "modules": [
                ("Введение в Python", 3, [
                    ("Установка и первая программа", "video", "https://example.com/py/1"),
                    ("Переменные и типы данных", "text", "https://example.com/py/2")]),
                ("Управляющие конструкции", 4, [
                    ("Условия и циклы", "video", "https://example.com/py/3"),
                    ("Функции", "text", "https://example.com/py/4")]),
            ],
        },
        {
            "title": "Основы баз данных",
            "description": "Реляционная модель, SQL-запросы, проектирование таблиц.",
            "level": "intermediate", "price": 49.9,
            "modules": [
                ("Реляционная модель", 3, [
                    ("Таблицы и ключи", "text", "https://example.com/db/1"),
                    ("Нормализация", "video", "https://example.com/db/2")]),
                ("Язык SQL", 5, [
                    ("SELECT и фильтрация", "video", "https://example.com/db/3"),
                    ("JOIN и агрегаты", "text", "https://example.com/db/4")]),
            ],
        },
        {
            "title": "Веб-разработка: HTML и CSS",
            "description": "Вёрстка страниц, адаптивный дизайн и основы JavaScript.",
            "level": "beginner", "price": 29.9,
            "modules": [
                ("Вёрстка страниц", 4, [
                    ("Теги и структура документа", "text", "https://example.com/web/1"),
                    ("Стили и селекторы", "video", "https://example.com/web/2")]),
                ("Адаптивный дизайн", 3, [
                    ("Flexbox и Grid", "video", "https://example.com/web/3"),
                    ("Медиазапросы", "text", "https://example.com/web/4")]),
            ],
        },
    ]

    result = []
    for course in catalog:
        course_id = _id()
        db.execute(
            "INSERT INTO courses (id, teacher_id, title, description, level, status, "
            "price, created_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (course_id, teacher_id, course["title"], course["description"],
             course["level"], "published", course["price"], _now(-30)))

        first_lesson_id = None
        for module_number, (module_title, hours, lessons) in enumerate(course["modules"], 1):
            module_id = _id()
            db.execute(
                "INSERT INTO modules (id, course_id, title, order_number, duration_hours) "
                "VALUES (?, ?, ?, ?, ?)",
                (module_id, course_id, module_title, module_number, hours))
            for lesson_number, (lesson_title, content_type, url) in enumerate(lessons, 1):
                lesson_id = _id()
                first_lesson_id = first_lesson_id or lesson_id
                db.execute(
                    "INSERT INTO lessons (id, module_id, title, content_type, content_url, "
                    "order_number) VALUES (?, ?, ?, ?, ?, ?)",
                    (lesson_id, module_id, lesson_title, content_type, url, lesson_number))
                db.execute(
                    "INSERT INTO materials (id, lesson_id, file_name, file_url, file_type) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (_id(), lesson_id, f"{lesson_title}.pdf",
                     f"{url}/material.pdf", "pdf"))

        result.append({"id": course_id, "first_lesson_id": first_lesson_id})
    return result
