"""WebinarService. Сигнатуры методов совпадают с диаграммой классов."""
from __future__ import annotations

import uuid
from datetime import datetime

from db.database import Database
from models.webinar import Webinar, WebinarAttendance
from models.user import Student
from services.mappers import load_user, parse_dt


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class WebinarService:
    def __init__(self, db: Database) -> None:
        self._db = db

    def createWebinar(self, title: str, date: datetime, courseId: uuid.UUID) -> Webinar:
        if not self._db.query_one("SELECT 1 FROM courses WHERE id = ?", (courseId,)):
            raise ValueError("Курс не найден")
        webinarId = uuid.uuid4()
        self._db.execute(
            "INSERT INTO webinars (id, course_id, title, scheduled_date, duration_minutes, "
            "recording_url, status) VALUES (?, ?, ?, ?, 60, NULL, 'scheduled')",
            (webinarId, courseId, title, date.isoformat(timespec="seconds")))
        row = self._db.query_one("SELECT * FROM webinars WHERE id = ?", (webinarId,))
        return Webinar(
            id=uuid.UUID(row["id"]), title=row["title"], scheduledDate=parse_dt(row["scheduled_date"]),
            durationMinutes=row["duration_minutes"], recordingUrl=row["recording_url"],
            status=row["status"])

    def startWebinar(self, id: uuid.UUID) -> str:
        """Переводит вебинар в статус 'live' и возвращает ссылку для подключения."""
        if self._db.query_one("SELECT 1 FROM webinars WHERE id = ?", (id,)) is None:
            raise ValueError("Вебинар не найден")
        self._db.execute("UPDATE webinars SET status = 'live' WHERE id = ?", (id,))
        return f"https://webinar.example.com/room/{id}"

    def joinWebinar(self, userId: uuid.UUID, webinarId: uuid.UUID) -> WebinarAttendance:
        if self._db.query_one("SELECT 1 FROM webinars WHERE id = ?", (webinarId,)) is None:
            raise ValueError("Вебинар не найден")
        attendanceId = uuid.uuid4()
        joinedAt = _now()
        self._db.execute(
            "INSERT INTO webinar_attendances (id, webinar_id, student_id, joined_at, left_at) "
            "VALUES (?, ?, ?, ?, NULL)", (attendanceId, webinarId, userId, joinedAt))
        student = load_user(self._db, userId)
        return WebinarAttendance(id=attendanceId, joinedAt=parse_dt(joinedAt),
                                 student=student if isinstance(student, Student) else None)

    def endWebinar(self, id: uuid.UUID) -> bool:
        """False, если вебинара не существует."""
        if self._db.query_one("SELECT 1 FROM webinars WHERE id = ?", (id,)) is None:
            return False
        self._db.execute("UPDATE webinars SET status = 'finished' WHERE id = ?", (id,))
        self._db.execute(
            "UPDATE webinar_attendances SET left_at = ? WHERE webinar_id = ? AND left_at IS NULL",
            (_now(), id))
        return True
