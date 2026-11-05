"""Преобразование строк БД в <<data>>-объекты (общее для нескольких сервисов)."""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from typing import Optional

from db.database import Database
from models.course import Course, Lesson, Material, Module
from models.user import Admin, Student, Teacher, User


def parse_dt(value: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(value) if value else None


def user_from_row(db: Database, row: sqlite3.Row) -> User:
    """Возвращает Student / Teacher / Admin в зависимости от роли."""
    base = dict(
        id=uuid.UUID(row["id"]), username=row["username"], password=row["password_hash"],
        fullName=row["full_name"], email=row["email"], role=row["role"],
    )
    role, user_id = row["role"], row["id"]
    uid = uuid.UUID(user_id)
    if role == "student":
        extra = db.query_one("SELECT * FROM students WHERE user_id = ?", (user_id,))
        if extra:
            return Student(**base, studentId=uid,
                           group=extra["student_group"], level=extra["level"])
    elif role == "teacher":
        extra = db.query_one("SELECT * FROM teachers WHERE user_id = ?", (user_id,))
        if extra:
            return Teacher(**base, teacherId=uid,
                           specialization=extra["specialization"], rating=extra["rating"])
    elif role == "admin":
        extra = db.query_one("SELECT * FROM admins WHERE user_id = ?", (user_id,))
        if extra:
            return Admin(**base, adminId=uid, accessLevel=extra["access_level"])
    return User(**base)


def load_user(db: Database, user_id: uuid.UUID) -> Optional[User]:
    row = db.query_one("SELECT * FROM users WHERE id = ?", (user_id,))
    return user_from_row(db, row) if row else None


def course_from_row(db: Database, row: sqlite3.Row, with_content: bool = False) -> Course:
    """with_content=True дополнительно загружает модули, уроки и материалы."""
    teacher = load_user(db, row["teacher_id"]) if row["teacher_id"] else None
    course = Course(
        id=uuid.UUID(row["id"]), title=row["title"], description=row["description"],
        level=row["level"], status=row["status"],
        createdDate=parse_dt(row["created_date"]), price=row["price"],
        teacher=teacher if isinstance(teacher, Teacher) else None,
    )
    if with_content:
        course.modules = _load_modules(db, course.id)
    return course


def load_course(db: Database, course_id: uuid.UUID, with_content: bool = False) -> Optional[Course]:
    row = db.query_one("SELECT * FROM courses WHERE id = ?", (course_id,))
    return course_from_row(db, row, with_content) if row else None


def _load_modules(db: Database, course_id: uuid.UUID) -> list[Module]:
    modules = []
    for m in db.query_all(
            "SELECT * FROM modules WHERE course_id = ? ORDER BY order_number", (course_id,)):
        lessons = []
        for l in db.query_all(
                "SELECT * FROM lessons WHERE module_id = ? ORDER BY order_number", (m["id"],)):
            materials = [
                Material(id=uuid.UUID(x["id"]), fileName=x["file_name"],
                         fileUrl=x["file_url"], fileType=x["file_type"])
                for x in db.query_all("SELECT * FROM materials WHERE lesson_id = ?", (l["id"],))
            ]
            lessons.append(Lesson(
                id=uuid.UUID(l["id"]), title=l["title"], contentType=l["content_type"],
                contentUrl=l["content_url"], orderNumber=l["order_number"],
                materials=materials))
        modules.append(Module(
            id=uuid.UUID(m["id"]), title=m["title"], orderNumber=m["order_number"],
            durationHours=m["duration_hours"], lessons=lessons))
    return modules
