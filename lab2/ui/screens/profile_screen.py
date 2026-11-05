"""Профиль (состояние «Профиль» из диаграммы; макета в ЛР1 нет)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from models.user import Student
from ui.helpers import logout
from ui.theme import ROLE_LABELS, initials


class ProfileScreen(ttk.Frame):
    def __init__(self, parent: tk.Misc, ui) -> None:
        super().__init__(parent)
        self.ui = ui
        page = ttk.Frame(self, padding=32)
        page.pack(fill="both", expand=True)

        ttk.Button(page, text="← Главное окно", style="Ghost.TButton",
                   command=lambda: ui.showScreen("main")).pack(anchor="w")
        ttk.Label(page, text="Профиль", style="Title.TLabel").pack(anchor="w", pady=(16, 14))

        card = ttk.Frame(page, style="Card.TFrame", padding=18)
        card.pack(fill="x")
        row = ttk.Frame(card)
        row.pack(anchor="w")
        self._avatar = ttk.Label(row, style="Avatar.TLabel")
        self._avatar.pack(side="left", padx=(0, 12))
        who = ttk.Frame(row)
        who.pack(side="left")
        self._name = ttk.Label(who, style="Bold.TLabel")
        self._name.pack(anchor="w")
        self._details = ttk.Label(who, style="Muted.TLabel")
        self._details.pack(anchor="w")

        ttk.Button(page, text="🚪  Выйти", style="Danger.TButton",
                   command=lambda: logout(ui)).pack(anchor="w", pady=(24, 0))

    def showProfile(self) -> None:
        user = self.ui.user
        self._avatar.configure(text=initials(user.fullName))
        self._name.configure(text=user.fullName)
        details = f"{user.email} · {ROLE_LABELS.get(user.role, user.role)}"
        if isinstance(user, Student) and user.group:
            details += f" · группа {user.group}"
        self._details.configure(text=details)
