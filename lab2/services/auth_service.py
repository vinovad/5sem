"""AuthService. Сигнатуры методов совпадают с диаграммой классов."""
from __future__ import annotations

import uuid
from typing import Optional

from db.database import Database
from db.security import hash_password, verify_password
from models.user import User
from services.mappers import load_user, user_from_row

ROLES = ("student", "teacher", "admin")


class AuthenticationError(Exception):
    """Неверный логин или пароль (в диаграмме поведение при ошибке не описано)."""


class AuthService:
    def __init__(self, db: Database) -> None:
        self._db = db
        self._currentUser: Optional[User] = None

    # Параметр `pass` из диаграммы в Python зарезервирован, поэтому он назван `password`.
    def registerUser(self, username: str, password: str, role: str) -> User:
        if role not in ROLES:
            raise ValueError(f"Неизвестная роль: {role}")
        if not username or not password:
            raise ValueError("Логин и пароль не могут быть пустыми")
        if self._db.query_one("SELECT 1 FROM users WHERE username = ?", (username,)):
            raise ValueError("Пользователь с таким логином уже существует")

        userId = uuid.uuid4()
        # Имя и почта в сигнатуре не предусмотрены, поэтому заполняются по умолчанию
        self._db.execute(
            "INSERT INTO users (id, username, password_hash, full_name, email, role) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (userId, username, hash_password(password), username,
             f"{username}@example.com", role))
        if role == "student":
            self._db.execute("INSERT INTO students (user_id, student_group, level) "
                             "VALUES (?, '', 'beginner')", (userId,))
        elif role == "teacher":
            self._db.execute("INSERT INTO teachers (user_id, specialization, rating) "
                             "VALUES (?, '', 0)", (userId,))
        else:
            self._db.execute("INSERT INTO admins (user_id, access_level) VALUES (?, 1)",
                             (userId,))
        return load_user(self._db, userId)

    def login(self, username: str, password: str) -> User:
        row = self._db.query_one("SELECT * FROM users WHERE username = ?", (username,))
        if row is None or not verify_password(password, row["password_hash"]):
            raise AuthenticationError("Неверный логин или пароль")
        self._currentUser = user_from_row(self._db, row)
        return self._currentUser

    def logout(self) -> None:
        self._currentUser = None

    def checkAccess(self, userId: uuid.UUID, role: str) -> bool:
        user = load_user(self._db, userId)
        return user is not None and (user.role == role or user.role == "admin")
