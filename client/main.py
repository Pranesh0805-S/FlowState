import os
import sys

from PyQt5.QtWidgets import QApplication

THIS_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(THIS_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from client.app import AppWindow
from client.screens.calendar import CalendarScreen
from client.screens.create_task import CreateTaskScreen
from client.screens.dashboard import DashboardScreen
from client.screens.forgot_password import ForgotPasswordScreen
from client.screens.history import HistoryScreen
from client.screens.index import IndexScreen
from client.screens.login import LoginScreen
from client.screens.register import RegisterScreen
from client.screens.settings import SettingsScreen
from client.screens.team_tasks import TeamTasksScreen
from client.screens.verify_otp import VerifyOtpScreen
from client.screens.workflow import WorkflowScreen


def main():
    app = QApplication(sys.argv)
    qss_path = os.path.join(THIS_DIR, "theme.qss")
    try:
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except Exception:
        pass

    window = AppWindow(
        screens=[
            IndexScreen,
            LoginScreen,
            RegisterScreen,
            VerifyOtpScreen,
            ForgotPasswordScreen,
            DashboardScreen,
            WorkflowScreen,
            CreateTaskScreen,
            TeamTasksScreen,
            HistoryScreen,
            CalendarScreen,
            SettingsScreen,
        ],
        start_route="index",
    )
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
