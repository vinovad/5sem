"""<<data>>: курс и его содержимое (Course → Module → Lesson → Material)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from models.user import Teacher


@dataclass
class Material:
    id: uuid.UUID
    fileName: str
    fileUrl: str
    fileType: str


@dataclass
class Lesson:
    id: uuid.UUID
    title: str
    contentType: str
    contentUrl: str
    orderNumber: int
    materials: list[Material] = field(default_factory=list)  # роль +materials


@dataclass
class Module:
    id: uuid.UUID
    title: str
    orderNumber: int
    durationHours: float
    lessons: list[Lesson] = field(default_factory=list)  # роль +lessons


@dataclass
class Course:
    id: uuid.UUID
    title: str
    description: str
    level: str
    status: str
    createdDate: datetime
    price: float = 0.0  # нет в базовой диаграмме, но есть в ER, в расширении №3 и в макете
    teacher: Optional[Teacher] = None                    # роль +teacher
    modules: list[Module] = field(default_factory=list)  # роль +modules
