"""MainUi  <<UI>>: главное окно приложения и 6 обработчиков из диаграммы классов.

AuthService.login() возвращает общий <<data>>-объект User, поэтому окно после входа
выбирается через if/else по полю role (см. PROBLEMS.md, п. 1).
"""
from __future__ import annotations

import tkinter as tk
import uuid
from tkinter import messagebox, ttk
from typing import Optional

from models.user import User
from services.auth_service import AuthenticationError, AuthService
from services.course_service import CourseService
from services.notification_service import NotificationService
from services.progress_service import ProgressService
from services.webinar_service import WebinarService
from ui import theme
from ui.helpers import showUnavailable
from ui.screens.catalog_screen import CatalogScreen
from ui.screens.course_screen import CourseScreen
from ui.screens.login_screen import AuthErrorScreen, LoginScreen
from ui.screens.main_screen import MainScreen
from ui.screens.profile_screen import ProfileScreen
from ui.screens.teacher_dashboard_screen import TeacherDashboardScreen
from ui.screens.webinar_screen import WebinarScreen

# имя окна -> (класс, имя входного действия из диаграммы состояний UI)
SCREENS = {
    "login": (LoginScreen, "showLoginForm"),
    "error": (AuthErrorScreen, "showError"),
    "main": (MainScreen, "show"),
    "catalog": (CatalogScreen, "displayCourses"),
    "course": (CourseScreen, "displayCourse"),
    "webinar": (WebinarScreen, "displayWebinar"),
    "profile": (ProfileScreen, "showProfile"),
    "dashboard": (TeacherDashboardScreen, "displayDashboard"),
}


class MainUi:
    def __init__(self, authService: AuthService, courseService: CourseService,
                 progressService: ProgressService, webinarService: WebinarService,
                 notificationService: NotificationService) -> None:
        # связи MainUi → сервисы (роли из диаграммы)
        self.authService = authService
        self.courseService = courseService
        self.progressService = progressService
        self.webinarService = webinarService
        self.notificationService = notificationService

        self.user: Optional[User] = None          # результат login
        self.selectedCourseId: Optional[uuid.UUID] = None  # обработчики по диаграмме без параметров

        self.root = tk.Tk()
        self.root.title("Платформа дистанционного обучения")
        self.root.geometry("1040x700")
        self.root.minsize(900, 600)
        theme.setup_styles(self.root)

        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self.screens = {}
        for name, (screenClass, _) in SCREENS.items():
            screen = screenClass(container, self)
            screen.grid(row=0, column=0, sticky="nsew")
            self.screens[name] = screen

        self.showScreen("login")

    # ---------- навигация ----------

    def showScreen(self, name: str, *args) -> None:
        """Показывает окно и вызывает его входное действие (entry / ... в диаграмме)."""
        screen = self.screens[name]
        getattr(screen, SCREENS[name][1])(*args)
        screen.tkraise()

    # ---------- обработчики из диаграммы классов ----------

    def onLoginSubmit(self) -> None:
        username, password = self.screens["login"].getCredentials()
        try:
            user = self.authService.login(username, password)
        except AuthenticationError as error:
            self.user = None
            self.showScreen("error", str(error))
            return

        self.user = user
        if user.role == "student":
            self.showScreen("main")
        elif user.role == "teacher":
            self.showScreen("dashboard")
        else:
            # окна для администратора нет ни в макетах, ни в диаграмме состояний
            self.authService.logout()
            self.user = None
            self.showScreen("error", "Для роли «Администратор» окна в модели нет")

    def onRegisterClick(self) -> None:
        username, password = self.screens["login"].getCredentials()
        try:
            # роль в форме входа не выбирается и в диаграмме не описана: создаётся учащийся
            self.authService.registerUser(username, password, "student")
        except ValueError as error:
            messagebox.showwarning("Регистрация", str(error))
            return
        messagebox.showinfo("Регистрация", "Аккаунт учащегося создан. Теперь можно войти.")

    def onCourseEnrollClick(self) -> None:
        if self.user is None or self.selectedCourseId is None:
            return
        if self.courseService.enrollStudent(self.user.id, self.selectedCourseId):
            messagebox.showinfo("Запись на курс", "Вы успешно записаны на курс.")
        else:
            messagebox.showinfo("Запись на курс", "Вы уже записаны на этот курс.")

    def onJoinWebinarClick(self) -> None:
        """Только переход в окно вебинара (как в диаграмме состояний): joinWebinar
        требует webinarId, получить который нечем (PROBLEMS.md, п. 4)."""
        self.showScreen("webinar")

    def onLeaveReviewClick(self) -> None:
        """В модели нет сервиса, который сохраняет отзыв (PROBLEMS.md, п. 5)."""
        showUnavailable("В модели нет сервиса, который сохраняет отзывы "
                             "(есть класс Review, но нет ReviewService).")

    def onViewProgressClick(self) -> None:
        """Обработчик есть в диаграмме классов, но ни в макетах, ни в диаграмме состояний
        нет элемента, который его вызывает (PROBLEMS.md, п. 6). Поэтому он не подключён."""
