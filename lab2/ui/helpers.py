"""Вспомогательные функции интерфейса.

Вынесены из MainUi, чтобы в этом классе остались только методы из диаграммы классов
(конструктор, 6 обработчиков) и showScreen для переходов диаграммы состояний.
"""
from __future__ import annotations

from tkinter import messagebox

from ui.theme import MUTED, TEXT


def showUnavailable(reason: str) -> None:
    """Элемент показан по макету, но модель не позволяет его реализовать."""
    messagebox.showinfo("Недоступно в модели", f"{reason}\n\nПодробности: PROBLEMS.md")


def logout(ui) -> None:
    """Разлогиниться в диаграмме состояний ведёт в конечное состояние."""
    ui.authService.logout()
    ui.user = None
    ui.root.destroy()


def setPlaceholder(entry, text: str) -> None:
    """Серая подсказка в поле ввода: исчезает при клике, возвращается, если поле пустое."""
    entry.insert(0, text)
    entry.configure(foreground=MUTED)

    def onFocusIn(event) -> None:
        if entry.get() == text:
            entry.delete(0, "end")
            entry.configure(foreground=TEXT)

    def onFocusOut(event) -> None:
        if not entry.get():
            entry.insert(0, text)
            entry.configure(foreground=MUTED)

    entry.bind("<FocusIn>", onFocusIn)
    entry.bind("<FocusOut>", onFocusOut)
