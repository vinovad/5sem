"""Главное окно учащегося (макет MainWindow)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ui.helpers import logout
from ui.theme import ROLE_LABELS, clear, initials

# раздел боковой панели -> почему его содержимое недоступно
SECTIONS = {
    "Мои курсы": "в CourseService нет метода получения курсов учащегося.",
    "Расписание": "в WebinarService нет метода получения списка вебинаров.",
}


class MainScreen(ttk.Frame):
    def __init__(self, parent: tk.Misc, ui) -> None:
        super().__init__(parent)
        self.ui = ui

        sidebar = ttk.Frame(self, style="Sidebar.TFrame", padding=16)
        sidebar.pack(side="left", fill="y")

        card = ttk.Frame(sidebar, style="Sidebar.TFrame")
        card.pack(fill="x", pady=(0, 18))
        self._avatar = ttk.Label(card, style="Avatar.TLabel")
        self._avatar.pack(side="left", padx=(0, 10))
        who = ttk.Frame(card, style="Sidebar.TFrame")
        who.pack(side="left")
        self._name = ttk.Label(who, style="SidebarBold.TLabel")
        self._name.pack(anchor="w")
        self._role = ttk.Label(who, style="SidebarMuted.TLabel")
        self._role.pack(anchor="w")

        def nav(text, command):
            ttk.Button(sidebar, text=text, style="Nav.TButton", command=command, width=20
                       ).pack(fill="x", pady=2)

        nav("📚  Каталог курсов", lambda: ui.showScreen("catalog"))
        nav("🎯  Мои курсы", lambda: self._render("Мои курсы"))
        nav("📅  Расписание", lambda: self._render("Расписание"))
        nav("👤  Профиль", lambda: ui.showScreen("profile"))
        nav("🚪  Выйти", lambda: logout(ui))

        self._content = ttk.Frame(self, padding=32)
        self._content.pack(side="left", fill="both", expand=True)

    def show(self) -> None:
        user = self.ui.user
        self._avatar.configure(text=initials(user.fullName))
        self._name.configure(text=user.fullName)
        self._role.configure(text=ROLE_LABELS.get(user.role, user.role))
        self._render(None)

    def _render(self, section) -> None:
        content = self._content
        clear(content)

        if section is not None:
            ttk.Label(content, text=section, style="Title.TLabel").pack(anchor="w")
            note = ttk.Frame(content, style="Card.TFrame", padding=18)
            note.pack(fill="x", pady=(22, 0))
            ttk.Label(note, text=f"Раздел недоступен: {SECTIONS[section]}",
                      style="Muted.TLabel").pack(anchor="w")
            ttk.Button(note, text="← На главную", style="Ghost.TButton",
                       command=lambda: self._render(None)).pack(anchor="w", pady=(14, 0))
            return

        user = self.ui.user
        parts = user.fullName.split()
        ttk.Label(content, text=f"Добрый день, {parts[0] if parts else user.username}!",
                  style="Title.TLabel").pack(anchor="w")
        ttk.Label(content, text="Продолжайте обучение", style="Muted.TLabel"
                  ).pack(anchor="w", pady=(2, 22))
        ttk.Label(content, text="📅  Ближайшие события", style="Heading.TLabel"
                  ).pack(anchor="w", pady=(0, 10))

        events = ttk.Frame(content, style="Card.TFrame", padding=18)
        events.pack(fill="x")
        ttk.Label(events, text="Список вебинаров недоступен: в модели нет метода "
                               "для его получения.", style="Muted.TLabel").pack(anchor="w")
        ttk.Button(events, text="Перейти по ссылке на вебинар", style="Accent.TButton",
                   command=self.ui.onJoinWebinarClick).pack(anchor="w", pady=(14, 0))
