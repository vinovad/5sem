"""CourseService. Сигнатуры методов совпадают с диаграммой классов."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from db.database import Database
from models.course import Course, Material
from services.mappers import course_from_row, load_course


class CourseService:
    def __init__(self, db: Database) -> None:
        self._db = db

    def createCourse(self, title: str, desc: str, price: float) -> Course:
        # Преподаватель и уровень в сигнатуре не предусмотрены: курс создаётся без них
        courseId = uuid.uuid4()
        self._db.execute(
            "INSERT INTO courses (id, teacher_id, title, description, level, status, "
            "price, created_date) VALUES (?, NULL, ?, ?, 'beginner', 'published', ?, ?)",
            (courseId, title, desc, price, datetime.now().isoformat(timespec="seconds")))
        return load_course(self._db, courseId)

    def getCatalog(self) -> list[Course]:
        rows = self._db.query_all(
            "SELECT * FROM courses WHERE status = 'published' ORDER BY title")
        return [course_from_row(self._db, r) for r in rows]

    def getCourse(self, id: uuid.UUID) -> Optional[Course]:
        """Курс вместе с модулями, уроками и материалами."""
        return load_course(self._db, id, with_content=True)

    def enrollStudent(self, studentId: uuid.UUID, courseId: uuid.UUID) -> bool:
        """False, если курса или студента нет либо студент уже записан."""
        if not self._db.query_one("SELECT 1 FROM courses WHERE id = ?", (courseId,)):
            return False
        if not self._db.query_one("SELECT 1 FROM users WHERE id = ?", (studentId,)):
            return False
        if self._db.query_one(
                "SELECT 1 FROM enrollments WHERE student_id = ? AND course_id = ?",
                (studentId, courseId)):
            return False
        self._db.execute(
            "INSERT INTO enrollments (student_id, course_id, enrolled_date) VALUES (?, ?, ?)",
            (studentId, courseId, datetime.now().isoformat(timespec="seconds")))
        return True

    def publishMaterial(self, lessonId: uuid.UUID, material: Material) -> bool:
        """False, если урока не существует."""
        if not self._db.query_one("SELECT 1 FROM lessons WHERE id = ?", (lessonId,)):
            return False
        self._db.execute(
            "INSERT INTO materials (id, lesson_id, file_name, file_url, file_type) "
            "VALUES (?, ?, ?, ?, ?)",
            (material.id, lessonId, material.fileName,
             material.fileUrl, material.fileType))
        return True
