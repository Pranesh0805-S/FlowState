from typing import Dict, List, Tuple

from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QPushButton, QVBoxLayout, QWidget


class Sidebar(QFrame):
    EXPANDED_WIDTH = 220
    COLLAPSED_WIDTH = 70

    NAV_ITEMS: List[Tuple[str, str, str]] = [
        ("dashboard", "Dashboard", "📊"),
        ("workflow", "Workflow", "🧩"),
        ("create_task", "Create Task", "➕"),
        ("calendar", "Calendar", "📅"),
        ("history", "History", "🕘"),
        ("team_tasks", "Team Tasks", "👥"),
        ("settings", "Settings", "⚙️"),
    ]

    def __init__(self, app_window, active_route: str = "dashboard"):
        super().__init__()
        self.app_window = app_window
        self.active_route = active_route
        self._expanded = True
        self._buttons: Dict[str, QPushButton] = {}
        self._labels: Dict[str, str] = {}
        self._icons: Dict[str, str] = {}

        self.setObjectName("Sidebar")
        self.setMinimumWidth(self.EXPANDED_WIDTH)
        self.setMaximumWidth(self.EXPANDED_WIDTH)

        self._anim = QPropertyAnimation(self, b"minimumWidth", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._anim.valueChanged.connect(self._sync_max_width)

        outer = QVBoxLayout()
        outer.setContentsMargins(10, 12, 10, 12)
        outer.setSpacing(8)

        self.toggle_btn = QPushButton("☰  Menu")
        self.toggle_btn.setObjectName("SidebarToggle")
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.clicked.connect(self.toggle)
        outer.addWidget(self.toggle_btn)

        self.nav_wrap = QVBoxLayout()
        self.nav_wrap.setContentsMargins(0, 8, 0, 8)
        self.nav_wrap.setSpacing(6)

        for route, label, icon in self.NAV_ITEMS:
            btn = QPushButton(f"{icon}  {label}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setObjectName("SidebarNavBtn")
            btn.setMinimumHeight(44)
            btn.clicked.connect(lambda _, r=route: self.app_window.navigate(r))
            self._buttons[route] = btn
            self._labels[route] = label
            self._icons[route] = icon
            self.nav_wrap.addWidget(btn)

        outer.addLayout(self.nav_wrap)
        outer.addStretch(1)

        self.logout_btn = QPushButton("🚪  Logout")
        self.logout_btn.setObjectName("SidebarNavBtn")
        self.logout_btn.setCursor(Qt.PointingHandCursor)
        self.logout_btn.setMinimumHeight(44)
        self.logout_btn.clicked.connect(self.app_window.logout)
        outer.addWidget(self.logout_btn)
        self.setLayout(outer)

        self.set_active(active_route)

    def _sync_max_width(self, width):
        width_int = int(width)
        self.setMaximumWidth(width_int)

    def set_active(self, route: str):
        self.active_route = route
        for key, btn in self._buttons.items():
            btn.setProperty("active", key == route)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def toggle(self):
        start = self.minimumWidth()
        end = self.COLLAPSED_WIDTH if self._expanded else self.EXPANDED_WIDTH
        self._anim.stop()
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        self._anim.start()
        self._expanded = not self._expanded
        self._apply_collapsed_state()

    def _apply_collapsed_state(self):
        collapsed = not self._expanded
        self.toggle_btn.setText("☰" if collapsed else "☰  Menu")

        for route, btn in self._buttons.items():
            icon = self._icons[route]
            label = self._labels[route]
            btn.setText(icon if collapsed else f"{icon}  {label}")
            btn.setToolTip(label if collapsed else "")

        self.logout_btn.setText("🚪" if collapsed else "🚪  Logout")
        self.logout_btn.setToolTip("Logout" if collapsed else "")

