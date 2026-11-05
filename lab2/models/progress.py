"""<<data>>: прогресс обучения и отзывы."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from models.course import Course
from models.user import User


@dataclass
class Progress:
    id: uuid.UUID
    status: str
    score: int
    startedDate: datetime
    completedDate: Optional[datetime] = None
    user: Optional[User] = None      # роль +user
    course: Optional[Course] = None  # роль +course


@dataclass
class Review:
    id: uuid.UUID
    rating: int
    text: str
    createdDate: datetime
    isApproved: bool
    user: Optional[User] = None      # роль +user
    course: Optional[Course] = None  # роль +course
