"""Панель преподавателя (макет TeacherDashboard)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ui.helpers import logout, showUnavailable
from ui.theme import (COURSE_ICONS, ICON_STYLES, LEVEL_LABELS, STATUS_LABELS,
                      ScrollableFrame, clear, plural)

MY_COURSES = "Мои курсы"
# вкладка -> почему её содержимое недоступно (None: вкладка работает)
TABS = {
    MY_COURSES: None,
    "Вебинары": "в WebinarService нет метода получения списка вебинаров.",
    "Задания": "в модели нет заданий (ни класса, ни сервиса).",
    "Правила": "в модели нет правил (ни класса, ни сервиса).",
}


class TeacherDashboardScreen(ttk.Frame):
    def __init__(self, parent: tk.Misc, ui) -> None:
        super().__init__(parent)
        self.ui = ui
        self._scroll = ScrollableFrame(self)
        self._scroll.pack(fill="both", expand=True)
        self._rows: list[tuple] = []  # (курс, число уроков)
        self._tab = MY_COURSES

    def displayDashboard(self) -> None:
        user = self.ui.user
        courses = [c for c in self.ui.courseService.getCatalog()
                   if c.teacher is not None and c.teacher.id == user.id]
        self._rows = []
        for course in courses:
            full = self.ui.courseService.getCourse(course.id)
            lessons = sum(len(m.lessons) for m in full.modules) if full else 0
            self._rows.append((course, lessons))
        self._tab = MY_COURSES
        self._render()

    def _openTab(self, name: str) -> None:
        self._tab = name
        self._render()

    def _render(self) -> None:
        body = self._scroll.body
        clear(body)
        self._scroll.scrollToTop()
        user = self.ui.user

        page = ttk.Frame(body, padding=32)
        page.pack(fill="both", expand=True)

        active = sum(1 for course, _ in self._rows if course.status == "published")
        subtitle = (f"{user.fullName} · {active} "
                    f"{plural(active, 'активный курс', 'активных курса', 'активных курсов')}")
        subtitle += " · студентов: —"  # в модели нет метода подсчёта студентов курса

        top = ttk.Frame(page)
        top.pack(fill="x")
        titles = ttk.Frame(top)
        titles.pack(side="left")
        ttk.Label(titles, text="Панель преподавателя", style="Title.TLabel").pack(anchor="w")
        ttk.Label(titles, text=subtitle, style="Muted.TLabel").pack(anchor="w")
        ttk.Button(top, text="🚪  Выйти", style="Danger.TButton", command=lambda: logout(self.ui)
                   ).pack(side="right", padx=(8, 0))
        ttk.Button(top, text="+ Создать курс", style="Accent.TButton",
                   command=lambda: showUnavailable(
                       "В MainUi нет обработчика создания курса, а createCourse не принимает "
                       "преподавателя, поэтому курс нельзя связать с ним.")).pack(side="right")

        tabs = ttk.Frame(page, style="Tabs.TFrame", padding=4)
        tabs.pack(anchor="w", pady=(20, 14))
        for name in TABS:
            style = "TabActive.TButton" if name == self._tab else "Tab.TButton"
            ttk.Button(tabs, text=name, style=style,
                       command=lambda n=name: self._openTab(n)).pack(side="left", padx=2)

        reason = TABS[self._tab]
        if reason is not None:
            note = ttk.Frame(page, style="Card.TFrame", padding=18)
            note.pack(fill="x")
            ttk.Label(note, text=f"Раздел недоступен: {reason}", style="Muted.TLabel"
                      ).pack(anchor="w")
            return

        for index, (course, lessons) in enumerate(self._rows):
            row = ttk.Frame(page, style="Card.TFrame", padding=14)
            row.pack(fill="x", pady=5)
            ttk.Label(row, text=COURSE_ICONS[index % len(COURSE_ICONS)],
                      style=ICON_STYLES[index % len(ICON_STYLES)]).pack(side="left", padx=(0, 14))
            info = ttk.Frame(row)
            info.pack(side="left")
            ttk.Label(info, text=course.title, style="Bold.TLabel").pack(anchor="w")
            ttk.Label(info, style="Muted.TLabel",
                      text=f"{STATUS_LABELS.get(course.status, course.status)} · "
                           f"{lessons} {plural(lessons, 'урок', 'урока', 'уроков')} · "
                           f"{LEVEL_LABELS.get(course.level, course.level)}").pack(anchor="w")
            ttk.Button(row, text="✏️", style="Ghost.TButton", width=3,
                       command=lambda: showUnavailable(
                           "В CourseService нет метода редактирования курса.")
                       ).pack(side="right")
            # в макете здесь число студентов и рейтинг курса; в модели их получить нельзя
            for caption in ("рейтинг", "студентов"):
                stat = ttk.Frame(row)
                stat.pack(side="right", padx=14)
                ttk.Label(stat, text="—", style="Bold.TLabel").pack()
                ttk.Label(stat, text=caption, style="Muted.TLabel").pack()
