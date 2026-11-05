"""Тесты реализации (unittest, без внешних зависимостей).

Запуск из папки проекта:

    python -m unittest -v        (или: python test.py)

Тесты окон пропускаются, если нет tkinter или графического окружения.
"""
from __future__ import annotations

import dataclasses
import inspect
import unittest
import uuid
from datetime import datetime, timedelta
from unittest import mock

from db.database import Database
from db.security import hash_password, verify_password
from db.seed import seed_if_empty
from models import course as course_models
from models import progress as progress_models
from models import user as user_models
from models import webinar as webinar_models
from models.course import Material
from models.user import Admin, Student, Teacher, User
from services import notification_service
from services.auth_service import AuthenticationError, AuthService
from services.course_service import CourseService
from services.notification_service import NotificationService
from services.progress_service import ProgressService
from services.webinar_service import WebinarService

try:
    import tkinter as tk
    HAS_TK = True
except ImportError:  # pragma: no cover
    tk = None
    HAS_TK = False

STUDENT, TEACHER, ADMIN = "student@gmail.com", "prepod@gmail.com", "admin@gmail.com"
PASSWORD = "1234"


class BaseCase(unittest.TestCase):
    """БД в памяти с тестовыми данными и все сервисы."""

    def setUp(self) -> None:
        self.db = Database(":memory:")
        self.db.init_schema()
        seed_if_empty(self.db)
        self.auth = AuthService(self.db)
        self.courses = CourseService(self.db)
        self.progress = ProgressService(self.db)
        self.webinars = WebinarService(self.db)
        self.notifications = NotificationService(self.db)

    def tearDown(self) -> None:
        self.db.close()

    def count(self, table: str) -> int:
        return self.db.query_one(f"SELECT COUNT(*) AS n FROM {table}")["n"]

    def course(self, prefix: str):
        return next(c for c in self.courses.getCatalog() if c.title.startswith(prefix))


# ---------------------------------------------------------------- БД и пароли

class SecurityTests(unittest.TestCase):
    def test_correct_password_is_accepted(self):
        self.assertTrue(verify_password("1234", hash_password("1234")))

    def test_wrong_password_is_rejected(self):
        self.assertFalse(verify_password("bad", hash_password("1234")))

    def test_hash_is_salted(self):
        self.assertNotEqual(hash_password("1234"), hash_password("1234"))

    def test_hash_does_not_contain_password(self):
        self.assertNotIn("1234", hash_password("1234"))

    def test_malformed_stored_value_is_rejected(self):
        self.assertFalse(verify_password("1234", "не хэш"))


class DatabaseTests(unittest.TestCase):
    def test_new_database_is_empty(self):
        db = Database(":memory:")
        db.init_schema()
        self.assertTrue(db.is_empty())

    def test_init_schema_can_run_twice(self):
        db = Database(":memory:")
        db.init_schema()
        db.init_schema()

    def test_seed_fills_database(self):
        db = Database(":memory:")
        db.init_schema()
        seed_if_empty(db)
        self.assertFalse(db.is_empty())
        counts = {t: db.query_one(f"SELECT COUNT(*) AS n FROM {t}")["n"]
                  for t in ("users", "courses", "modules", "lessons", "materials", "webinars")}
        self.assertEqual(counts, {"users": 3, "courses": 3, "modules": 6,
                                  "lessons": 12, "materials": 12, "webinars": 1})

    def test_seed_does_not_duplicate_data(self):
        db = Database(":memory:")
        db.init_schema()
        seed_if_empty(db)
        seed_if_empty(db)
        self.assertEqual(db.query_one("SELECT COUNT(*) AS n FROM users")["n"], 3)

    def test_uuid_can_be_used_as_query_parameter(self):
        db = Database(":memory:")
        db.init_schema()
        seed_if_empty(db)
        row = db.query_one("SELECT id FROM users LIMIT 1")
        self.assertIsNotNone(
            db.query_one("SELECT 1 FROM users WHERE id = ?", (uuid.UUID(row["id"]),)))


# ---------------------------------------------------------------- модели

class ModelTests(unittest.TestCase):
    DATA_CLASSES = [
        user_models.User, user_models.Admin, user_models.Student, user_models.Teacher,
        course_models.Course, course_models.Module, course_models.Lesson, course_models.Material,
        webinar_models.Webinar, webinar_models.WebinarAttendance,
        progress_models.Progress, progress_models.Review,
    ]

    # атрибуты из диаграммы классов (связи-роли проверяются отдельно)
    ATTRIBUTES = {
        User: ["id", "username", "password", "fullName", "email", "role"],
        Admin: ["adminId", "accessLevel"],
        Student: ["studentId", "group", "level"],
        Teacher: ["teacherId", "specialization", "rating"],
        course_models.Course: ["id", "title", "description", "level", "status",
                               "createdDate", "price"],  # price: см. PROBLEMS.md
        course_models.Module: ["id", "title", "orderNumber", "durationHours"],
        course_models.Lesson: ["id", "title", "contentType", "contentUrl", "orderNumber"],
        course_models.Material: ["id", "fileName", "fileUrl", "fileType"],
        webinar_models.Webinar: ["id", "title", "scheduledDate", "durationMinutes",
                                 "recordingUrl", "status"],
        webinar_models.WebinarAttendance: ["id", "joinedAt", "leftAt"],
        progress_models.Progress: ["id", "status", "score", "startedDate", "completedDate"],
        progress_models.Review: ["id", "rating", "text", "createdDate", "isApproved"],
    }
    ROLES = {
        course_models.Course: ["teacher", "modules"],
        course_models.Module: ["lessons"],
        course_models.Lesson: ["materials"],
        webinar_models.Webinar: ["attendances"],
        webinar_models.WebinarAttendance: ["student"],
        progress_models.Progress: ["user", "course"],
        progress_models.Review: ["user", "course"],
    }

    def test_data_classes_have_no_methods(self):
        for cls in self.DATA_CLASSES:
            methods = [n for n, f in inspect.getmembers(cls, inspect.isfunction)
                       if not n.startswith("_")]
            self.assertEqual(methods, [], cls.__name__)

    def test_attributes_match_diagram(self):
        for cls, expected in self.ATTRIBUTES.items():
            own = [f.name for f in dataclasses.fields(cls)]
            if cls in (Admin, Student, Teacher):
                own = [n for n in own if n not in self.ATTRIBUTES[User]]
            plain = [n for n in own if n not in self.ROLES.get(cls, [])]
            self.assertEqual(plain, expected, cls.__name__)

    def test_association_roles_exist(self):
        for cls, roles in self.ROLES.items():
            names = {f.name for f in dataclasses.fields(cls)}
            for role in roles:
                self.assertIn(role, names, f"{cls.__name__}.{role}")

    def test_inheritance_from_user(self):
        for cls in (Admin, Student, Teacher):
            self.assertTrue(issubclass(cls, User))

    def test_composition_defaults_are_independent_lists(self):
        a = course_models.Module(uuid.uuid4(), "m", 1, 1.0)
        b = course_models.Module(uuid.uuid4(), "m", 2, 1.0)
        a.lessons.append(object())
        self.assertEqual(b.lessons, [])


# ---------------------------------------------------------------- соответствие диаграмме

class DiagramConformanceTests(unittest.TestCase):
    METHODS = {
        AuthService: {"registerUser": ["username", "password", "role"],  # pass -> password
                      "login": ["username", "password"], "logout": [],
                      "checkAccess": ["userId", "role"]},
        CourseService: {"createCourse": ["title", "desc", "price"], "getCatalog": [],
                        "getCourse": ["id"], "enrollStudent": ["studentId", "courseId"],
                        "publishMaterial": ["lessonId", "material"]},
        WebinarService: {"createWebinar": ["title", "date", "courseId"],
                         "startWebinar": ["id"], "joinWebinar": ["userId", "webinarId"],
                         "endWebinar": ["id"]},
        NotificationService: {"notifyUser": ["userId", "message"],
                              "notifyCourseStudents": ["courseId"]},
        ProgressService: {"updateProgress": ["userId", "lessonId", "score"],
                          "getStudentProgress": ["userId"]},
    }

    def test_service_methods_and_parameters(self):
        for cls, spec in self.METHODS.items():
            public = {n for n, _ in inspect.getmembers(cls, inspect.isfunction)
                      if not n.startswith("_")}
            self.assertEqual(public, set(spec), f"методы {cls.__name__}")
            for name, params in spec.items():
                actual = [p for p in inspect.signature(getattr(cls, name)).parameters
                          if p != "self"]
                self.assertEqual(actual, params, f"{cls.__name__}.{name}")

    def test_services_have_no_private_methods(self):
        for cls in self.METHODS:
            private = [n for n, _ in inspect.getmembers(cls, inspect.isfunction)
                       if n.startswith("_") and not n.startswith("__")]
            self.assertEqual(private, [], cls.__name__)


# ---------------------------------------------------------------- AuthService

class AuthServiceTests(BaseCase):
    def test_login_student_returns_student(self):
        user = self.auth.login(STUDENT, PASSWORD)
        self.assertIsInstance(user, Student)
        self.assertEqual(user.role, "student")
        self.assertEqual(user.fullName, "Иван Петров")
        self.assertEqual(user.group, "421702")

    def test_login_teacher_returns_teacher(self):
        user = self.auth.login(TEACHER, PASSWORD)
        self.assertIsInstance(user, Teacher)
        self.assertEqual(user.rating, 4.8)

    def test_login_admin_returns_admin(self):
        self.assertIsInstance(self.auth.login(ADMIN, PASSWORD), Admin)

    def test_identifiers_are_uuid(self):
        user = self.auth.login(STUDENT, PASSWORD)
        self.assertIsInstance(user.id, uuid.UUID)
        self.assertEqual(user.studentId, user.id)

    def test_wrong_password(self):
        with self.assertRaises(AuthenticationError):
            self.auth.login(STUDENT, "wrong")

    def test_unknown_user(self):
        with self.assertRaises(AuthenticationError):
            self.auth.login("nobody@gmail.com", PASSWORD)

    def test_empty_credentials(self):
        with self.assertRaises(AuthenticationError):
            self.auth.login("", "")

    def test_register_student_and_login(self):
        created = self.auth.registerUser("maria@gmail.com", "pw", "student")
        self.assertIsInstance(created, Student)
        self.assertEqual(self.auth.login("maria@gmail.com", "pw").id, created.id)

    def test_register_teacher(self):
        self.assertIsInstance(self.auth.registerUser("t2@gmail.com", "pw", "teacher"), Teacher)

    def test_register_stores_hash_not_password(self):
        self.auth.registerUser("maria@gmail.com", "secret", "student")
        row = self.db.query_one("SELECT password_hash FROM users WHERE username = ?",
                                ("maria@gmail.com",))
        self.assertNotIn("secret", row["password_hash"])

    def test_register_duplicate_login(self):
        with self.assertRaises(ValueError):
            self.auth.registerUser(STUDENT, "pw", "student")

    def test_register_unknown_role(self):
        with self.assertRaises(ValueError):
            self.auth.registerUser("x@gmail.com", "pw", "hacker")

    def test_register_empty_fields(self):
        with self.assertRaises(ValueError):
            self.auth.registerUser("", "pw", "student")
        with self.assertRaises(ValueError):
            self.auth.registerUser("x@gmail.com", "", "student")

    def test_check_access(self):
        student = self.auth.login(STUDENT, PASSWORD)
        admin = self.auth.login(ADMIN, PASSWORD)
        self.assertTrue(self.auth.checkAccess(student.id, "student"))
        self.assertFalse(self.auth.checkAccess(student.id, "teacher"))
        self.assertTrue(self.auth.checkAccess(admin.id, "teacher"))
        self.assertFalse(self.auth.checkAccess(uuid.uuid4(), "student"))

    def test_logout_does_not_fail(self):
        self.auth.login(STUDENT, PASSWORD)
        self.auth.logout()
        self.auth.logout()


# ---------------------------------------------------------------- CourseService

class CourseServiceTests(BaseCase):
    def test_catalog_contains_published_courses(self):
        titles = {c.title for c in self.courses.getCatalog()}
        self.assertEqual(titles, {"Python для начинающих", "Основы баз данных",
                                  "Веб-разработка: HTML и CSS"})

    def test_catalog_courses_have_teacher_and_price(self):
        for c in self.courses.getCatalog():
            self.assertIsInstance(c.teacher, Teacher)
            self.assertIsInstance(c.id, uuid.UUID)
        self.assertEqual(self.course("Python").price, 0)
        self.assertGreater(self.course("Основы").price, 0)

    def test_get_course_returns_full_structure(self):
        full = self.courses.getCourse(self.course("Python").id)
        self.assertEqual(len(full.modules), 2)
        self.assertEqual([m.orderNumber for m in full.modules], [1, 2])
        for module in full.modules:
            self.assertEqual(len(module.lessons), 2)
            for lesson in module.lessons:
                self.assertEqual(len(lesson.materials), 1)

    def test_get_unknown_course(self):
        self.assertIsNone(self.courses.getCourse(uuid.uuid4()))

    def test_enroll_student(self):
        student = self.auth.login(STUDENT, PASSWORD)
        target = self.course("Основы")
        self.assertTrue(self.courses.enrollStudent(student.id, target.id))
        self.assertEqual(self.count("enrollments"), 2)

    def test_enroll_twice(self):
        student = self.auth.login(STUDENT, PASSWORD)
        target = self.course("Основы")
        self.courses.enrollStudent(student.id, target.id)
        self.assertFalse(self.courses.enrollStudent(student.id, target.id))

    def test_enroll_already_enrolled_in_seed(self):
        student = self.auth.login(STUDENT, PASSWORD)
        self.assertFalse(self.courses.enrollStudent(student.id, self.course("Python").id))

    def test_enroll_unknown_course_or_student(self):
        student = self.auth.login(STUDENT, PASSWORD)
        self.assertFalse(self.courses.enrollStudent(student.id, uuid.uuid4()))
        self.assertFalse(self.courses.enrollStudent(uuid.uuid4(), self.course("Python").id))

    def test_publish_material(self):
        full = self.courses.getCourse(self.course("Python").id)
        lesson = full.modules[0].lessons[0]
        material = Material(uuid.uuid4(), "slides.pdf", "https://example.com/s", "pdf")
        self.assertTrue(self.courses.publishMaterial(lesson.id, material))
        reloaded = self.courses.getCourse(full.id).modules[0].lessons[0]
        self.assertIn("slides.pdf", [m.fileName for m in reloaded.materials])

    def test_publish_material_unknown_lesson(self):
        material = Material(uuid.uuid4(), "a.pdf", "u", "pdf")
        self.assertFalse(self.courses.publishMaterial(uuid.uuid4(), material))

    def test_create_course(self):
        created = self.courses.createCourse("Новый курс", "Описание", 10.0)
        self.assertEqual(created.title, "Новый курс")
        self.assertEqual(created.price, 10.0)
        self.assertIsNone(created.teacher)
        self.assertIn(created.id, [c.id for c in self.courses.getCatalog()])


# ---------------------------------------------------------------- ProgressService

class ProgressServiceTests(BaseCase):
    def setUp(self) -> None:
        super().setUp()
        self.student = self.auth.login(STUDENT, PASSWORD)
        self.lesson = self.courses.getCourse(self.course("Python").id).modules[0].lessons[1]

    def test_seed_progress(self):
        items = self.progress.getStudentProgress(self.student.id)
        self.assertEqual(len(items), 1)
        self.assertEqual((items[0].status, items[0].score), ("completed", 90))
        self.assertEqual(items[0].course.title, "Python для начинающих")
        self.assertEqual(items[0].user.id, self.student.id)

    def test_low_score_is_in_progress(self):
        self.progress.updateProgress(self.student.id, self.lesson.id, 40)
        last = self.progress.getStudentProgress(self.student.id)[-1]
        self.assertEqual((last.status, last.score), ("in_progress", 40))
        self.assertIsNone(last.completedDate)

    def test_passing_score_is_completed(self):
        self.progress.updateProgress(self.student.id, self.lesson.id, 60)
        last = self.progress.getStudentProgress(self.student.id)[-1]
        self.assertEqual(last.status, "completed")
        self.assertIsNotNone(last.completedDate)

    def test_update_does_not_duplicate_records(self):
        self.progress.updateProgress(self.student.id, self.lesson.id, 40)
        self.progress.updateProgress(self.student.id, self.lesson.id, 85)
        items = self.progress.getStudentProgress(self.student.id)
        self.assertEqual(len(items), 2)
        self.assertEqual((items[-1].status, items[-1].score), ("completed", 85))

    def test_unknown_lesson(self):
        with self.assertRaises(ValueError):
            self.progress.updateProgress(self.student.id, uuid.uuid4(), 50)

    def test_user_without_progress(self):
        other = self.auth.registerUser("new@gmail.com", "pw", "student")
        self.assertEqual(self.progress.getStudentProgress(other.id), [])


# ---------------------------------------------------------------- WebinarService

class WebinarServiceTests(BaseCase):
    def setUp(self) -> None:
        super().setUp()
        self.student = self.auth.login(STUDENT, PASSWORD)
        self.course_id = self.course("Python").id
        self.webinar = self.webinars.createWebinar(
            "Тестовый вебинар", datetime.now() + timedelta(days=1), self.course_id)

    def status(self) -> str:
        return self.db.query_one("SELECT status FROM webinars WHERE id = ?",
                                 (self.webinar.id,))["status"]

    def test_create_webinar(self):
        self.assertEqual(self.webinar.title, "Тестовый вебинар")
        self.assertEqual(self.webinar.status, "scheduled")
        self.assertIsInstance(self.webinar.id, uuid.UUID)
        self.assertEqual(self.count("webinars"), 2)

    def test_create_webinar_for_unknown_course(self):
        with self.assertRaises(ValueError):
            self.webinars.createWebinar("X", datetime.now(), uuid.uuid4())

    def test_start_webinar(self):
        link = self.webinars.startWebinar(self.webinar.id)
        self.assertIn(str(self.webinar.id), link)
        self.assertEqual(self.status(), "live")

    def test_start_unknown_webinar(self):
        with self.assertRaises(ValueError):
            self.webinars.startWebinar(uuid.uuid4())

    def test_join_webinar(self):
        attendance = self.webinars.joinWebinar(self.student.id, self.webinar.id)
        self.assertIsInstance(attendance.id, uuid.UUID)
        self.assertIsInstance(attendance.student, Student)
        self.assertEqual(attendance.student.id, self.student.id)
        self.assertIsNone(attendance.leftAt)
        self.assertEqual(self.count("webinar_attendances"), 1)

    def test_join_unknown_webinar(self):
        with self.assertRaises(ValueError):
            self.webinars.joinWebinar(self.student.id, uuid.uuid4())

    def test_end_webinar(self):
        self.webinars.joinWebinar(self.student.id, self.webinar.id)
        self.assertTrue(self.webinars.endWebinar(self.webinar.id))
        self.assertEqual(self.status(), "finished")
        left = self.db.query_one("SELECT left_at FROM webinar_attendances")["left_at"]
        self.assertIsNotNone(left)

    def test_end_unknown_webinar(self):
        self.assertFalse(self.webinars.endWebinar(uuid.uuid4()))


# ---------------------------------------------------------------- NotificationService

class NotificationServiceTests(BaseCase):
    def test_notify_user_writes_log(self):
        with self.assertLogs("services.notification_service", level="INFO") as logs:
            self.notifications.notifyUser(uuid.uuid4(), "Привет")
        self.assertIn("Привет", logs.output[0])

    def test_notify_course_students_reaches_enrolled_student(self):
        with self.assertLogs("services.notification_service", level="INFO") as logs:
            self.notifications.notifyCourseStudents(self.course("Python").id)
        self.assertEqual(len(logs.output), 1)
        self.assertIn("Python для начинающих", logs.output[0])

    def test_notify_course_without_students(self):
        with mock.patch.object(notification_service.logger, "info") as info:
            self.notifications.notifyCourseStudents(self.course("Основы").id)
        info.assert_not_called()

    def test_notify_unknown_course(self):
        with mock.patch.object(notification_service.logger, "info") as info:
            self.notifications.notifyCourseStudents(uuid.uuid4())
        info.assert_not_called()


# ---------------------------------------------------------------- интерфейс

@unittest.skipUnless(HAS_TK, "tkinter не установлен")
class UiTests(BaseCase):
    HANDLERS = {"onLoginSubmit", "onRegisterClick", "onCourseEnrollClick",
                "onJoinWebinarClick", "onLeaveReviewClick", "onViewProgressClick"}

    def setUp(self) -> None:
        super().setUp()
        from ui import helpers
        from ui.main_ui import MainUi
        self.helpers = helpers
        try:
            self.ui = MainUi(self.auth, self.courses, self.progress,
                             self.webinars, self.notifications)
        except tk.TclError:
            self.skipTest("нет графического окружения")
        patcher_main = mock.patch("ui.main_ui.messagebox")
        patcher_help = mock.patch("ui.helpers.messagebox")
        self.messagebox = patcher_main.start()
        self.helpMessagebox = patcher_help.start()
        self.addCleanup(patcher_main.stop)
        self.addCleanup(patcher_help.stop)
        self.addCleanup(self.destroyWindow)

    def destroyWindow(self) -> None:
        try:
            self.ui.root.destroy()
        except tk.TclError:
            pass

    def login(self, username: str, password: str = PASSWORD) -> None:
        form = self.ui.screens["login"]
        form._username.set(username)
        form._password.set(password)
        self.ui.onLoginSubmit()

    def test_main_ui_has_only_diagram_methods(self):
        from ui.main_ui import MainUi
        public = {n for n, _ in inspect.getmembers(MainUi, inspect.isfunction)
                  if not n.startswith("_")}
        self.assertEqual(public, self.HANDLERS | {"showScreen"})

    def test_main_ui_is_linked_to_all_services(self):
        self.assertIs(self.ui.authService, self.auth)
        self.assertIs(self.ui.courseService, self.courses)
        self.assertIs(self.ui.progressService, self.progress)
        self.assertIs(self.ui.webinarService, self.webinars)
        self.assertIs(self.ui.notificationService, self.notifications)

    def test_all_screens_created(self):
        self.assertEqual(set(self.ui.screens), {"login", "error", "main", "catalog",
                                                "course", "webinar", "profile", "dashboard"})

    def test_student_login_opens_main_window(self):
        with mock.patch.object(self.ui, "showScreen", wraps=self.ui.showScreen) as show:
            self.login(STUDENT)
        show.assert_called_with("main")
        self.assertEqual(self.ui.user.role, "student")

    def test_teacher_login_opens_dashboard(self):
        with mock.patch.object(self.ui, "showScreen", wraps=self.ui.showScreen) as show:
            self.login(TEACHER)
        show.assert_called_with("dashboard")
        self.assertEqual(self.ui.user.role, "teacher")

    def test_wrong_password_shows_error_window(self):
        with mock.patch.object(self.ui, "showScreen", wraps=self.ui.showScreen) as show:
            self.login(STUDENT, "wrong")
        show.assert_called_with("error", "Неверный логин или пароль")
        self.assertIsNone(self.ui.user)

    def test_admin_has_no_window(self):
        with mock.patch.object(self.ui, "showScreen", wraps=self.ui.showScreen) as show:
            self.login(ADMIN)
        self.assertEqual(show.call_args[0][0], "error")
        self.assertIsNone(self.ui.user)

    def test_register_creates_student(self):
        self.ui.screens["login"]._username.set("maria@gmail.com")
        self.ui.screens["login"]._password.set("pw")
        self.ui.onRegisterClick()
        self.messagebox.showinfo.assert_called_once()
        self.assertIsInstance(self.auth.login("maria@gmail.com", "pw"), Student)

    def test_register_duplicate_shows_warning(self):
        self.ui.screens["login"]._username.set(STUDENT)
        self.ui.screens["login"]._password.set("pw")
        self.ui.onRegisterClick()
        self.messagebox.showwarning.assert_called_once()

    def test_enroll_uses_selected_course(self):
        self.login(STUDENT)
        self.ui.selectedCourseId = self.course("Основы").id
        self.ui.onCourseEnrollClick()
        self.assertIn("успешно", self.messagebox.showinfo.call_args[0][1])
        self.assertEqual(self.count("enrollments"), 2)

    def test_enroll_twice_reports_already_enrolled(self):
        self.login(STUDENT)
        self.ui.selectedCourseId = self.course("Основы").id
        self.ui.onCourseEnrollClick()
        self.ui.onCourseEnrollClick()
        self.assertIn("уже", self.messagebox.showinfo.call_args[0][1])
        self.assertEqual(self.count("enrollments"), 2)

    def test_enroll_without_login_does_nothing(self):
        self.ui.selectedCourseId = self.course("Основы").id
        self.ui.onCourseEnrollClick()
        self.messagebox.showinfo.assert_not_called()
        self.assertEqual(self.count("enrollments"), 1)

    def test_selecting_course_page_remembers_course(self):
        self.login(STUDENT)
        target = self.course("Основы")
        self.ui.showScreen("course", target.id)
        self.assertEqual(self.ui.selectedCourseId, target.id)

    def test_join_webinar_opens_webinar_window(self):
        with mock.patch.object(self.ui, "showScreen", wraps=self.ui.showScreen) as show:
            self.ui.onJoinWebinarClick()
        show.assert_called_once_with("webinar")

    def test_leave_review_explains_missing_model_part(self):
        self.ui.onLeaveReviewClick()
        self.helpMessagebox.showinfo.assert_called_once()

    def test_view_progress_has_no_side_effects(self):
        self.ui.onViewProgressClick()
        self.messagebox.showinfo.assert_not_called()

    def test_student_screens_open(self):
        self.login(STUDENT)
        for name, args in (("main", ()), ("catalog", ()), ("profile", ()), ("webinar", ()),
                           ("course", (self.course("Python").id,))):
            self.ui.showScreen(name, *args)

    def test_unknown_course_page_does_not_crash(self):
        self.login(STUDENT)
        self.ui.showScreen("course", uuid.uuid4())

    def test_teacher_dashboard_shows_only_own_courses(self):
        self.login(TEACHER)
        self.ui.showScreen("dashboard")
        rows = self.ui.screens["dashboard"]._rows
        self.assertEqual(len(rows), 3)
        for course, lessons in rows:
            self.assertEqual(lessons, 4)

    def test_teacher_without_courses_sees_empty_dashboard(self):
        self.auth.registerUser("t2@gmail.com", "pw", "teacher")
        self.login("t2@gmail.com", "pw")
        self.assertEqual(self.ui.screens["dashboard"]._rows, [])

    def test_logout_helper_clears_user(self):
        self.login(STUDENT)
        self.helpers.logout(self.ui)
        self.assertIsNone(self.ui.user)

    def test_show_unavailable_uses_message_box(self):
        self.helpers.showUnavailable("причина")
        self.assertIn("причина", self.helpMessagebox.showinfo.call_args[0][1])


if __name__ == "__main__":
    unittest.main(verbosity=2)