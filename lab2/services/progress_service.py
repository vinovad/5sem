"""ProgressService. Сигнатуры методов совпадают с диаграммой классов."""
from __future__ import annotations

import uuid
from datetime import datetime

from db.database import Database
from models.progress import Progress
from services.mappers import load_course, load_user, parse_dt

PASS_SCORE = 60  # с этого балла урок считается пройденным


class ProgressService:
    def __init__(self, db: Database) -> None:
        self._db = db

    def updateProgress(self, userId: uuid.UUID, lessonId: uuid.UUID, score: int) -> None:
        lesson = self._db.query_one(
            "SELECT m.course_id FROM lessons l JOIN modules m ON m.id = l.module_id "
            "WHERE l.id = ?", (lessonId,))
        if lesson is None:
            raise ValueError("Урок не найден")

        now = datetime.now().isoformat(timespec="seconds")
        completed = score >= PASS_SCORE
        status = "completed" if completed else "in_progress"
        completedDate = now if completed else None

        existing = self._db.query_one(
            "SELECT id FROM progress WHERE user_id = ? AND lesson_id = ?", (userId, lessonId))
        if existing:
            self._db.execute(
                "UPDATE progress SET status = ?, score = ?, completed_date = ? WHERE id = ?",
                (status, score, completedDate, existing["id"]))
        else:
            self._db.execute(
                "INSERT INTO progress (id, user_id, course_id, lesson_id, status, score, "
                "started_date, completed_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (uuid.uuid4(), userId, lesson["course_id"], lessonId,
                 status, score, now, completedDate))

    def getStudentProgress(self, userId: uuid.UUID) -> list[Progress]:
        user = load_user(self._db, userId)
        rows = self._db.query_all(
            "SELECT * FROM progress WHERE user_id = ? ORDER BY started_date", (userId,))
        return [
            Progress(
                id=uuid.UUID(r["id"]), status=r["status"], score=r["score"],
                startedDate=parse_dt(r["started_date"]),
                completedDate=parse_dt(r["completed_date"]),
                user=user, course=load_course(self._db, r["course_id"]))
            for r in rows
        ]
