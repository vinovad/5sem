"""Каталог курсов (макет CatalogWindow)."""
from __future__ import annotations

import tkinter as tk
import uuid
from tkinter import ttk

from ui.helpers import setPlaceholder, showUnavailable
from ui.theme import (COURSE_ICONS, ICON_STYLES, LEVEL_LABELS, ScrollableFrame,
                      clear)


PLACEHOLDER = "🔍  Поиск курса..."


class CatalogScreen(ttk.Frame):
    def __init__(self, parent: tk.Misc, ui) -> None:
        super().__init__(parent)
        self.ui = ui
        self._scroll = ScrollableFrame(self)
        self._scroll.pack(fill="both", expand=True)

    def displayCourses(self) -> None:
        body = self._scroll.body
        clear(body)
        self._scroll.scrollToTop()
        courses = self.ui.courseService.getCatalog()

        page = ttk.Frame(body, padding=32)
        page.pack(fill="both", expand=True)
        ttk.Button(page, text="← Главное окно", style="Ghost.TButton",
                   command=lambda: self.ui.showScreen("main")).pack(anchor="w")
        ttk.Label(page, text="Каталог курсов", style="Title.TLabel"
                  ).pack(anchor="w", pady=(16, 0))
        ttk.Label(page, text=f"Найдите подходящий курс из {len(courses)} доступных",
                  style="Muted.TLabel").pack(anchor="w", pady=(2, 16))
        search = ttk.Entry(page)
        setPlaceholder(search, PLACEHOLDER)
        search.pack(fill="x", pady=(0, 16))
        search.bind("<Return>", lambda e: showUnavailable(
            "В CourseService нет метода поиска курсов (есть только getCatalog)."))

        grid = ttk.Frame(page)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1, uniform="col")
        grid.columnconfigure(1, weight=1, uniform="col")

        for index, course in enumerate(courses):
            card = ttk.Frame(grid, style="Card.TFrame", padding=16)
            card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=8, pady=8)

            ttk.Label(card, text=COURSE_ICONS[index % len(COURSE_ICONS)],
                      style=ICON_STYLES[index % len(ICON_STYLES)]).pack(anchor="w")
            ttk.Label(card, text=course.title, style="Bold.TLabel"
                      ).pack(anchor="w", pady=(10, 0))
            teacher = course.teacher.fullName if course.teacher else "преподаватель не указан"
            ttk.Label(card, text=teacher, style="Muted.TLabel").pack(anchor="w", pady=(2, 8))

            tags = ttk.Frame(card)
            tags.pack(anchor="w", pady=(0, 12))
            ttk.Label(tags, text=LEVEL_LABELS.get(course.level, course.level),
                      style="TagGrey.TLabel").pack(side="left", padx=(0, 6))
            free = course.price == 0
            ttk.Label(tags, text="Бесплатно" if free else "Платный",
                      style="TagGreen.TLabel" if free else "TagOrange.TLabel"
                      ).pack(side="left")

            buttons = ttk.Frame(card)
            buttons.pack(anchor="w")
            ttk.Button(buttons, text="Подробнее", style="Ghost.TButton",
                       command=lambda c=course: self.ui.showScreen("course", c.id)
                       ).pack(side="left", padx=(0, 8))
            ttk.Button(buttons, text="Записаться", style="Accent.TButton",
                       command=lambda c=course: self._enroll(c.id)).pack(side="left")

    def _enroll(self, courseId: uuid.UUID) -> None:
        # onCourseEnrollClick() по диаграмме без параметров, поэтому курс запоминается заранее
        self.ui.selectedCourseId = courseId
        self.ui.onCourseEnrollClick()
