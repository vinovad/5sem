"""<<data>>: вебинар и посещаемость."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from models.user import Student


@dataclass
class WebinarAttendance:
    id: uuid.UUID
    joinedAt: datetime
    leftAt: Optional[datetime] = None
    student: Optional[Student] = None  # связь с Student (роль на диаграмме не названа)


@dataclass
class Webinar:
    id: uuid.UUID
    title: str
    scheduledDate: datetime
    durationMinutes: int
    recordingUrl: Optional[str]
    status: str
    attendances: list[WebinarAttendance] = field(default_factory=list)  # роль +attendances
