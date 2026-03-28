from typing import Dict, List, Type

from PyQt5.QtWidgets import QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget

from .services.api_client import ApiClient
from .widgets.nav_bar import NavBar
from .widgets.sidebar import Sidebar


class BaseScreen(QWidget):
    route_name: str = "base"
    route_title: str = "Screen"
    show_nav: bool = False

    def __init__(self, app_window: "AppWindow", api: ApiClient):
        super().__init__()
        self.app_window = app_window
        self.api = api

    def on_show(self):
        """Called when screen becomes active."""

    def refresh(self):
        """Called when user clicks Refresh."""
        self.on_show()


class AuthenticatedScreen(BaseScreen):
    show_nav = False

    def build_shell(self, active_route: str, page_title: str, content_widget: QWidget):
        self.sidebar = Sidebar(self.app_window, active_route=active_route)
        self.navbar = NavBar(self.app_window, page_title)
        if self.api.user:
            self.navbar.update_avatar(self.api.user.get("name", ""))

        right = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addWidget(self.navbar)
        right_layout.addWidget(content_widget, 1)
        right.setLayout(right_layout)

        root = QHBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self.sidebar, 0)
        root.addWidget(right, 1)
        self.setLayout(root)

    def on_show(self):
        if self.api.user:
            self.navbar.update_avatar(self.api.user.get("name", ""))


class AppWindow(QWidget):
    def __init__(self, screens: List[Type[BaseScreen]], start_route: str):
        super().__init__()
        self.api = ApiClient()
        self.pending_verification_email: str = ""
        self.setWindowTitle("Productivity Automation System")
        self.setMinimumSize(1366, 768)

        self.stack = QStackedWidget()

        self._routes: Dict[str, int] = {}
        self._route_order: List[str] = []
        self._history: List[str] = []
        self._history_index: int = -1

        for cls in screens:
            widget = cls(self, self.api)
            idx = self.stack.addWidget(widget)
            self._routes[widget.route_name] = idx
            self._route_order.append(widget.route_name)

        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self.stack, 1)
        self.setLayout(root)

        self.navigate(start_route, push_history=True)

    def current_screen(self) -> BaseScreen:
        return self.stack.currentWidget()  # type: ignore[return-value]

    def navigate(self, route_name: str, push_history: bool = True):
        if route_name not in self._routes:
            return
        idx = self._routes[route_name]
        self.stack.setCurrentIndex(idx)

        screen = self.current_screen()
        if push_history:
            if self._history_index < len(self._history) - 1:
                self._history = self._history[: self._history_index + 1]
            self._history.append(route_name)
            self._history_index = len(self._history) - 1
        screen.on_show()

    def go_back(self):
        if self._history_index <= 0:
            return
        self._history_index -= 1
        self.navigate(self._history[self._history_index], push_history=False)

    def go_next(self):
        if self._history_index >= len(self._history) - 1:
            return
        self._history_index += 1
        self.navigate(self._history[self._history_index], push_history=False)

    def refresh_current(self):
        self.current_screen().refresh()

    def logout(self):
        self.api.clear_auth()
        self.navigate("login")

    def notify(self, message: str, title: str = "Info"):
        self.setWindowTitle(f"Productivity Automation System | {title}: {message}")

    def ensure_logged_in(self) -> bool:
        return bool(self.api.token and self.api.user)
