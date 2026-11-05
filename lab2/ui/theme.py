"""Цвета, стили ttk и небольшие вспомогательные виджеты (общие для всех окон)."""
from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk

BG = "#ffffff"
SIDEBAR = "#f6f7fb"
BORDER = "#e3e6ef"
TEXT = "#1c1d2e"
MUTED = "#7b8096"
ACCENT = "#667eea"
ACCENT_DARK = "#5568d3"
ACCENT_SOFT = "#e9ecff"
DANGER = "#d64545"
DANGER_SOFT = "#fdecec"
DARK = "#161a33"
FONT = "Helvetica"

LEVEL_LABELS = {"beginner": "Начальный", "intermediate": "Средний", "advanced": "Продвинутый"}
STATUS_LABELS = {"published": "Опубликован", "draft": "Черновик"}
ROLE_LABELS = {"student": "Учащийся", "teacher": "Преподаватель", "admin": "Администратор"}
ICON_STYLES = ["Icon.TLabel", "IconGreen.TLabel", "IconOrange.TLabel"]
COURSE_ICONS = ["🐍", "🗄️", "🤖", "🌐", "📊", "🧮"]


def setup_styles(root: tk.Tk) -> None:
    s = ttk.Style(root)
    s.theme_use("clam")
    s.configure(".", background=BG, foreground=TEXT, font=(FONT, 11))

    s.configure("TFrame", background=BG)
    s.configure("Sidebar.TFrame", background=SIDEBAR)
    s.configure("Dark.TFrame", background=DARK)
    s.configure("Tabs.TFrame", background="#eff1f7")
    s.configure("Card.TFrame", background=BG, borderwidth=1, relief="solid",
                bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)

    s.configure("TLabel", background=BG, foreground=TEXT)
    s.configure("Title.TLabel", font=(FONT, 22, "bold"))
    s.configure("Heading.TLabel", font=(FONT, 14, "bold"))
    s.configure("Bold.TLabel", font=(FONT, 12, "bold"))
    s.configure("Muted.TLabel", foreground=MUTED)
    s.configure("Danger.TLabel", foreground=DANGER, font=(FONT, 12, "bold"))
    s.configure("Icon.TLabel", font=(FONT, 28), background=ACCENT_SOFT, padding=12)
    for name, color in (("IconGreen", "#e3f5ea"), ("IconOrange", "#fdeedd")):
        s.configure(f"{name}.TLabel", font=(FONT, 28), background=color, padding=12)
    s.configure("Tag.TLabel", background=ACCENT_SOFT, foreground=ACCENT_DARK,
                font=(FONT, 9, "bold"), padding=(8, 3))
    s.configure("TagGrey.TLabel", background="#eef0f4", foreground=TEXT,
                font=(FONT, 9, "bold"), padding=(8, 3))
    s.configure("TagGreen.TLabel", background="#e3f5ea", foreground="#1f8a4c",
                font=(FONT, 9, "bold"), padding=(8, 3))
    s.configure("TagOrange.TLabel", background="#fdeedd", foreground="#c46a00",
                font=(FONT, 9, "bold"), padding=(8, 3))
    s.configure("Sidebar.TLabel", background=SIDEBAR)
    s.configure("SidebarBold.TLabel", background=SIDEBAR, font=(FONT, 12, "bold"))
    s.configure("SidebarMuted.TLabel", background=SIDEBAR, foreground=MUTED, font=(FONT, 10))
    s.configure("Dark.TLabel", background=DARK, foreground="#8890b5", font=(FONT, 28))
    s.configure("Avatar.TLabel", background=ACCENT, foreground="#ffffff",
                font=(FONT, 12, "bold"), padding=(10, 8))

    def button(name, bg, fg, active, disabled_bg, disabled_fg, bold=True, anchor="center"):
        s.configure(name, background=bg, foreground=fg, bordercolor=bg, lightcolor=bg,
                    darkcolor=bg, focuscolor=bg, padding=(16, 9), relief="flat",
                    borderwidth=1, anchor=anchor, font=(FONT, 11, "bold" if bold else "normal"))
        s.map(name,
              background=[("disabled", disabled_bg), ("active", active)],
              foreground=[("disabled", disabled_fg)],
              bordercolor=[("disabled", disabled_bg), ("active", active)],
              lightcolor=[("disabled", disabled_bg), ("active", active)],
              darkcolor=[("disabled", disabled_bg), ("active", active)])

    button("Accent.TButton", ACCENT, "#ffffff", ACCENT_DARK, "#c4caf5", "#ffffff")
    button("Ghost.TButton", "#eff1f7", TEXT, "#e2e5f0", "#f4f5f9", "#a9aec2")
    button("Danger.TButton", DANGER_SOFT, DANGER, "#f8d7d7", "#fbf3f3", "#e0b3b3")
    button("Tab.TButton", "#eff1f7", MUTED, "#e2e5f0", "#eff1f7", "#a9aec2")
    button("TabActive.TButton", BG, TEXT, BG, BG, "#a9aec2")
    button("Nav.TButton", SIDEBAR, TEXT, "#e6e9fb", SIDEBAR, "#a9aec2",
           bold=False, anchor="w")

    s.configure("TEntry", fieldbackground="#f7f8fc", bordercolor=BORDER, lightcolor=BORDER,
                darkcolor=BORDER, padding=8)
    s.map("TEntry", fieldbackground=[("disabled", "#eceef4")],
          foreground=[("disabled", MUTED)])


def plural(n: int, one: str, few: str, many: str) -> str:
    """Склонение по числу: 1 курс, 2 курса, 5 курсов."""
    if 11 <= n % 100 <= 14:
        return many
    return {1: one, 2: few, 3: few, 4: few}.get(n % 10, many)


def clear(widget: tk.Misc) -> None:
    """Удаляет все дочерние виджеты."""
    for child in widget.winfo_children():
        child.destroy()


def initials(text: str) -> str:
    return (text[:2] or "?").upper()


class ScrollableFrame(ttk.Frame):
    """Прокручиваемая область: содержимое добавляется в self.body."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self._canvas = tk.Canvas(self, highlightthickness=0, bg=BG, bd=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self.body = ttk.Frame(self._canvas)
        self._window = self._canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.body.bind("<Configure>", lambda e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfigure(
            self._window, width=e.width))
        self.bind("<Enter>", lambda e: self._bind_wheel())
        self.bind("<Leave>", lambda e: self._unbind_wheel())

    def _bind_wheel(self) -> None:
        self._canvas.bind_all("<MouseWheel>", self._on_wheel)
        self._canvas.bind_all("<Button-4>", lambda e: self._canvas.yview_scroll(-1, "units"))
        self._canvas.bind_all("<Button-5>", lambda e: self._canvas.yview_scroll(1, "units"))

    def _unbind_wheel(self) -> None:
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self._canvas.unbind_all(sequence)

    def _on_wheel(self, event: tk.Event) -> None:
        step = -event.delta if sys.platform == "darwin" else -event.delta // 120
        self._canvas.yview_scroll(int(step), "units")

    def scrollToTop(self) -> None:
        self._canvas.yview_moveto(0)
