"""Подключение к SQLite и создание схемы базы данных."""
from __future__ import annotations

import sqlite3
import uuid
from typing import Any, Iterable, Optional

# идентификаторы в БД хранятся строками, а в коде используются как uuid.UUID
sqlite3.register_adapter(uuid.UUID, str)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name     TEXT NOT NULL,
    email         TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('student', 'teacher', 'admin'))
);

CREATE TABLE IF NOT EXISTS students (
    user_id       TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    student_group TEXT NOT NULL,
    level         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS teachers (
    user_id        TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    specialization TEXT NOT NULL,
    rating         REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS admins (
    user_id      TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    access_level INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS courses (
    id           TEXT PRIMARY KEY,
    teacher_id   TEXT REFERENCES users(id),
    title        TEXT NOT NULL,
    description  TEXT NOT NULL,
    level        TEXT NOT NULL,
    status       TEXT NOT NULL,
    price        REAL NOT NULL DEFAULT 0,
    created_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS modules (
    id           TEXT PRIMARY KEY,
    course_id    TEXT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title        TEXT NOT NULL,
    order_number INTEGER NOT NULL,
    duration_hours REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS lessons (
    id           TEXT PRIMARY KEY,
    module_id    TEXT NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    title        TEXT NOT NULL,
    content_type TEXT NOT NULL,
    content_url  TEXT NOT NULL,
    order_number INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS materials (
    id        TEXT PRIMARY KEY,
    lesson_id TEXT NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_url  TEXT NOT NULL,
    file_type TEXT NOT NULL
);

-- Запись учащегося на курс (нужна для CourseService.enrollStudent)
CREATE TABLE IF NOT EXISTS enrollments (
    student_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id     TEXT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    enrolled_date TEXT NOT NULL,
    PRIMARY KEY (student_id, course_id)
);

CREATE TABLE IF NOT EXISTS progress (
    id             TEXT PRIMARY KEY,
    user_id        TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id      TEXT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    lesson_id      TEXT NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    status         TEXT NOT NULL,
    score          INTEGER NOT NULL DEFAULT 0,
    started_date   TEXT NOT NULL,
    completed_date TEXT,
    UNIQUE (user_id, lesson_id)
);

CREATE TABLE IF NOT EXISTS reviews (
    id           TEXT PRIMARY KEY,
    user_id      TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id    TEXT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    rating       INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    text         TEXT NOT NULL,
    created_date TEXT NOT NULL,
    is_approved  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS webinars (
    id               TEXT PRIMARY KEY,
    course_id        TEXT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title            TEXT NOT NULL,
    scheduled_date   TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL,
    recording_url    TEXT,
    status           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS webinar_attendances (
    id         TEXT PRIMARY KEY,
    webinar_id TEXT NOT NULL REFERENCES webinars(id) ON DELETE CASCADE,
    student_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    joined_at  TEXT NOT NULL,
    left_at    TEXT
);
"""


class Database:
    """Тонкая обёртка над sqlite3. Её получают сервисы через внедрение зависимостей."""

    def __init__(self, path: str = "app.db") -> None:
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")

    def init_schema(self) -> None:
        """Создаёт таблицы, если их ещё нет."""
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def is_empty(self) -> bool:
        """True, если в БД ещё нет ни одного пользователя (первый запуск)."""
        row = self._conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()
        return row["n"] == 0

    def execute(self, sql: str, params: Iterable[Any] = ()) -> sqlite3.Cursor:
        """Выполняет INSERT/UPDATE/DELETE и сразу фиксирует изменения."""
        cursor = self._conn.execute(sql, tuple(params))
        self._conn.commit()
        return cursor

    def query_all(self, sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
        return self._conn.execute(sql, tuple(params)).fetchall()

    def query_one(self, sql: str, params: Iterable[Any] = ()) -> Optional[sqlite3.Row]:
        return self._conn.execute(sql, tuple(params)).fetchone()

    def close(self) -> None:
        self._conn.close()
