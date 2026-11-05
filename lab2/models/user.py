"""<<data>>: пользователи системы (имена атрибутов как на диаграмме)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class User:
    id: uuid.UUID
    username: str
    password: str  # в БД хранится хэш пароля, а не открытый текст
    fullName: str
    email: str
    role: str


@dataclass
class Admin(User):
    adminId: uuid.UUID
    accessLevel: int


@dataclass
class Student(User):
    studentId: uuid.UUID
    group: str
    level: str


@dataclass
class Teacher(User):
    teacherId: uuid.UUID
    specialization: str
    rating: float
