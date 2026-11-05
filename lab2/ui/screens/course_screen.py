"""Страница курса (макет CourseWindow)."""
from __future__ import annotations

import tkinter as tk
import uuid
from tkinter import ttk

from ui.theme import LEVEL_LABELS, ScrollableFrame, clear


class CourseScreen(ttk.Frame):
    def __init__(self, parent: tk.Misc, ui) -> None:
        super().__init__(parent)
        self.ui = ui
        self._scroll = ScrollableFrame(self)
        self._scroll.pack(fill="both", expand=True)

    def displayCourse(self, courseId: uuid.UUID) -> None:
        body = self._scroll.body
        clear(body)
        self._scroll.scrollToTop()
        self.ui.selectedCourseId = courseId
        course = self.ui.courseService.getCourse(courseId)

        page = ttk.Frame(body, padding=32)
        page.pack(fill="both", expand=True)
        ttk.Button(page, text="← Каталог курсов", style="Ghost.TButton",
                   command=lambda: self.ui.showScreen("catalog")).pack(anchor="w")
        if course is None:
            ttk.Label(page, text="Курс не найден", style="Title.TLabel").pack(pady=20)
            return

        header = ttk.Frame(page)
        header.pack(fill="x", pady=(16, 0))
        ttk.Label(header, text="📘", style="Icon.TLabel").pack(side="left", padx=(0, 16))
        info = ttk.Frame(header)
        info.pack(side="left")
        ttk.Label(info, text=course.title, style="Title.TLabel").pack(anchor="w")
        teacher = course.teacher.fullName if course.teacher else "преподаватель не указан"
        lessons = sum(len(m.lessons) for m in course.modules)
        ttk.Label(info, style="Muted.TLabel",
                  text=f"{teacher} · {LEVEL_LABELS.get(course.level, course.level)} · "
                       f"уроков: {lessons}").pack(anchor="w")
        ttk.Button(header, text="Записаться", style="Accent.TButton",
                   command=self.ui.onCourseEnrollClick).pack(side="right")
        ttk.Label(page, text=course.description, style="Muted.TLabel",
                  wraplength=800, justify="left").pack(anchor="w", pady=(14, 0))

        ttk.Label(page, text="Программа курса", style="Heading.TLabel"
                  ).pack(anchor="w", pady=(24, 10))
        for module in course.modules:
            card = ttk.Frame(page, style="Card.TFrame", padding=14)
            card.pack(fill="x", pady=5)
            top = ttk.Frame(card)
            top.pack(fill="x")
            ttk.Label(top, text=str(module.orderNumber), style="Avatar.TLabel"
                      ).pack(side="left", padx=(0, 10))
            ttk.Label(top, text=module.title, style="Bold.TLabel").pack(side="left")
            ttk.Label(top, text=f"{module.durationHours:g} ч", style="Muted.TLabel"
                      ).pack(side="right")
            for lesson in module.lessons:
                ttk.Label(card, text=f"●  {lesson.title}  ({lesson.contentType})"
                          ).pack(anchor="w", padx=(8, 0), pady=(8, 0))
                for material in lesson.materials:
                    ttk.Label(card, text=f"📎 {material.fileName}", style="Muted.TLabel"
                              ).pack(anchor="w", padx=(30, 0))

        ttk.Label(page, text="Отзывы", style="Heading.TLabel"
                  ).pack(anchor="w", pady=(24, 10))
        reviews = ttk.Frame(page, style="Card.TFrame", padding=14)
        reviews.pack(fill="x")
        ttk.Label(reviews, text="Отзывы недоступны: в модели нет метода для их получения.",
                  style="Muted.TLabel").pack(anchor="w")
        ttk.Button(reviews, text="Оставить отзыв", style="Ghost.TButton",
                   command=self.ui.onLeaveReviewClick).pack(anchor="w", pady=(12, 0))
