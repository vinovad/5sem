"""Окно вебинара (макет WebinarWindow)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ui.helpers import setPlaceholder, showUnavailable


class WebinarScreen(ttk.Frame):
    def __init__(self, parent: tk.Misc, ui) -> None:
        super().__init__(parent)
        self.ui = ui

        header = ttk.Frame(self, padding=(24, 16))
        header.pack(fill="x")
        titles = ttk.Frame(header)
        titles.pack(side="left")
        ttk.Label(titles, text="Вебинар", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(titles, text="Данные вебинара недоступны: в модели нет метода "
                               "для их получения.", style="Muted.TLabel").pack(anchor="w")

        main = ttk.Frame(self, padding=(24, 0, 24, 24))
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True)
        video = ttk.Frame(left, style="Dark.TFrame")
        video.pack(fill="both", expand=True)
        ttk.Label(video, text="🎥", style="Dark.TLabel").place(relx=0.5, rely=0.5,
                                                              anchor="center")
        buttons = ttk.Frame(left)
        buttons.pack(fill="x", pady=(12, 0))
        buttons.columnconfigure(0, weight=1, uniform="b")
        buttons.columnconfigure(1, weight=1, uniform="b")
        ttk.Button(buttons, text="⏹  Завершить", style="Danger.TButton",
                   command=lambda: showUnavailable(
                       "endWebinar(id) требует идентификатор вебинара, а окну он неизвестен: "
                       "в модели нет метода получения вебинара.")
                   ).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(buttons, text="🚪  Покинуть", style="Ghost.TButton",
                   command=lambda: ui.showScreen("main")
                   ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        chat = ttk.Frame(main, style="Card.TFrame", padding=12, width=280)
        chat.pack(side="right", fill="y", padx=(16, 0))
        chat.pack_propagate(False)
        ttk.Label(chat, text="💬  Чат", style="Bold.TLabel").pack(anchor="w")
        ttk.Label(chat, text="Сообщений пока нет.", style="Muted.TLabel"
                  ).pack(anchor="w", pady=(10, 0))
        noChat = lambda *args: showUnavailable("В модели нет чата вебинара "
                                                  "(ни класса, ни сервиса).")
        send = ttk.Frame(chat)
        send.pack(side="bottom", fill="x")
        message = ttk.Entry(send)
        setPlaceholder(message, "Ваше сообщение...")
        message.pack(side="left", fill="x", expand=True)
        message.bind("<Return>", noChat)
        ttk.Button(send, text="➤", style="Accent.TButton", width=3, command=noChat
                   ).pack(side="left", padx=(6, 0))

    def displayWebinar(self) -> None:
        """Входное действие состояния «ОкноВебинара»."""
