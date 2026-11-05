"""MainApplication  <<main, injector>>: создаёт БД, сервисы и интерфейс."""
from __future__ import annotations

import sys
from pathlib import Path

from db.database import Database
from db.seed import seed_if_empty
from services.auth_service import AuthService
from services.course_service import CourseService
from services.notification_service import NotificationService
from services.progress_service import ProgressService
from services.webinar_service import WebinarService
from ui.main_ui import MainUi

DB_PATH = Path(__file__).resolve().parent / "app.db"


class MainApplication:
    def main(self, args: list[str]) -> None:
        db = Database(str(DB_PATH))
        db.init_schema()
        seed_if_empty(db)

        # <<create>>: сервисы и UI создаются здесь и внедряются друг в друга
        authService = AuthService(db)
        courseService = CourseService(db)
        progressService = ProgressService(db)
        webinarService = WebinarService(db)
        notificationService = NotificationService(db)
        ui = MainUi(authService, courseService, progressService,
                    webinarService, notificationService)
        try:
            ui.root.mainloop()
        finally:
            db.close()


if __name__ == "__main__":
    MainApplication().main(sys.argv[1:])
