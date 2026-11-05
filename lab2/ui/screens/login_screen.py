"""Окно входа (макет LoginWindow) и окно ошибки авторизации (состояние из диаграммы)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ui.theme import FONT


class LoginScreen(ttk.Frame):
    def __init__(self, parent: tk.Misc, ui) -> None:
        super().__init__(parent)
        self.ui = ui
        self._username = tk.StringVar()
        self._password = tk.StringVar()

        inner = ttk.Frame(self)
        inner.place(relx=0.5, rely=0.45, anchor="center")

        ttk.Label(inner, text="🎓", style="Icon.TLabel").pack(pady=(0, 12))
        ttk.Label(inner, text="Добро пожаловать", style="Title.TLabel").pack()
        ttk.Label(inner, text="Войдите в образовательную платформу",
                  style="Muted.TLabel").pack(pady=(2, 22))

        ttk.Label(inner, text="Email", style="Bold.TLabel").pack(anchor="w", pady=(0, 4))
        self._usernameEntry = ttk.Entry(inner, textvariable=self._username, width=38,
                                        font=(FONT, 12))
        self._usernameEntry.pack(fill="x", pady=(0, 14))
        self._usernameEntry.bind("<Return>", lambda e: ui.onLoginSubmit())

        ttk.Label(inner, text="Пароль", style="Bold.TLabel").pack(anchor="w", pady=(0, 4))
        passwordEntry = ttk.Entry(inner, textvariable=self._password, show="•", width=38,
                                  font=(FONT, 12))
        passwordEntry.pack(fill="x", pady=(0, 18))
        passwordEntry.bind("<Return>", lambda e: ui.onLoginSubmit())

        ttk.Button(inner, text="Войти", style="Accent.TButton",
                   command=ui.onLoginSubmit).pack(fill="x")
        ttk.Label(inner, text="или", style="Muted.TLabel").pack(pady=10)
        ttk.Button(inner, text="Создать аккаунт", style="Ghost.TButton",
                   command=ui.onRegisterClick).pack(fill="x")

        ttk.Label(inner, style="Muted.TLabel", justify="center",
                  text="Тестовые аккаунты (пароль 1234):\n"
                       "student@gmail.com — учащийся, prepod@gmail.com — преподаватель, admin@gmail.com — администратор"
                  ).pack(pady=(22, 0))

    def showLoginForm(self) -> None:
        self._password.set("")
        self._usernameEntry.focus_set()

    def getCredentials(self) -> tuple[str, str]:
        return self._username.get().strip(), self._password.get()


class AuthErrorScreen(ttk.Frame):
    """Состояние «ОшибкаАвторизации»."""

    def __init__(self, parent: tk.Misc, ui) -> None:
        super().__init__(parent)
        self.ui = ui
        inner = ttk.Frame(self)
        inner.place(relx=0.5, rely=0.45, anchor="center")
        ttk.Label(inner, text="⚠️", font=(FONT, 36)).pack()
        ttk.Label(inner, text="Ошибка авторизации", style="Danger.TLabel").pack(pady=(6, 4))
        self._message = ttk.Label(inner, style="Muted.TLabel")
        self._message.pack(pady=(0, 18))
        ttk.Button(inner, text="Назад", style="Accent.TButton",
                   command=lambda: ui.showScreen("login")).pack()

    def showError(self, message: str) -> None:
        self._message.configure(text=message)
