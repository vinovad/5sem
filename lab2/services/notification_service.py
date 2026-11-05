"""NotificationService. Сигнатуры методов совпадают с диаграммой классов.

В диаграмме не описано, куда уходят уведомления, поэтому они пишутся в лог.
"""
from __future__ import annotations

import uuid
import logging

from db.database import Database

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: Database) -> None:
        self._db = db

    def notifyUser(self, userId: uuid.UUID, message: str) -> None:
        logger.info("Уведомление для %s: %s", userId, message)

    def notifyCourseStudents(self, courseId: uuid.UUID) -> None:
        # Текст в сигнатуре не предусмотрен, поэтому сообщение стандартное
        course = self._db.query_one("SELECT title FROM courses WHERE id = ?", (courseId,))
        if course is None:
            return
        message = f"Есть обновления по курсу «{course['title']}»"
        for row in self._db.query_all(
                "SELECT student_id FROM enrollments WHERE course_id = ?", (courseId,)):
            self.notifyUser(uuid.UUID(row["student_id"]), message)
