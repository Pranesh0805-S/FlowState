from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from ..app import AuthenticatedScreen


class HistoryScreen(AuthenticatedScreen):
    route_name = "history"
    route_title = "History"

    def __init__(self, app_window, api):
        super().__init__(app_window, api)
        self.status = QLabel("")
        self.status.setObjectName("Muted")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        page_wrap = QWidget()
        scroll.setWidget(page_wrap)

        self.timeline_layout = QVBoxLayout()
        self.timeline_layout.setContentsMargins(0, 0, 0, 0)
        self.timeline_layout.setSpacing(12)

        page = QVBoxLayout()
        page.setContentsMargins(20, 20, 20, 20)
        page.setSpacing(12)
        page.addWidget(self.status)
        page.addLayout(self.timeline_layout)
        page.addStretch(1)
        page_wrap.setLayout(page)

        self.build_shell("history", "History Timeline", scroll)

    def on_show(self):
        super().on_show()
        if not self.app_window.ensure_logged_in():
            self.app_window.navigate("login")
            return
        self.refresh()

    def refresh(self):
        self._clear_timeline()
        res = self.api.call("history.list", {"limit": 200})
        if res.get("status") != "success":
            self.status.setText(res.get("message", "Failed to load history"))
            return

        items = res.get("data", {}).get("items", [])
        if not items:
            empty = QLabel("No timeline events yet.")
            empty.setObjectName("Muted")
            self.timeline_layout.addWidget(empty)
            self.status.setText("")
            return

        for event in items:
            self.timeline_layout.addWidget(self._timeline_item(event))
        self.status.setText(f"{len(items)} events loaded")

    def _timeline_item(self, event: dict) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        badge_text, badge_color, icon = self._event_visuals(str(event.get("event", "")), str(event.get("status", "")))

        icon_dot = QLabel(icon)
        icon_dot.setFixedSize(26, 26)
        icon_dot.setStyleSheet("background:#EEF2FF; border-radius:13px;")
        icon_dot.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("Card")
        cl = QVBoxLayout()
        cl.setContentsMargins(12, 10, 12, 10)
        cl.setSpacing(6)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        title = QLabel(event.get("title", "Task"))
        title.setStyleSheet("font-weight: 700;")
        badge = QLabel(badge_text)
        badge.setStyleSheet(
            f"background:{badge_color}; color:#fff; border-radius:10px; padding:2px 8px; font-size:11px; font-weight:600;"
        )
        top.addWidget(title)
        top.addStretch(1)
        top.addWidget(badge)

        details = QLabel(f"{event.get('timestamp', '')} | status: {event.get('status', '')}")
        details.setObjectName("Muted")
        details.setWordWrap(True)

        cl.addLayout(top)
        cl.addWidget(details)
        card.setLayout(cl)

        layout.addWidget(icon_dot, 0)
        layout.addWidget(card, 1)
        row.setLayout(layout)
        return row

    def _event_visuals(self, event_name: str, status: str):
        ev = (event_name or "").lower()
        st = (status or "").lower()
        if ev == "created":
            return "Created", "#2563EB", "●"
        if st == "completed" or ev == "completed":
            return "Completed", "#16A34A", "✓"
        if ev in ("updated", "moved", "status_changed"):
            return "Updated", "#F59E0B", "↻"
        return "Updated", "#F59E0B", "↻"

    def _clear_timeline(self):
        while self.timeline_layout.count():
            item = self.timeline_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
