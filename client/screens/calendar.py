from PyQt5.QtCore import QDate
from PyQt5.QtGui import QColor, QTextCharFormat
from PyQt5.QtWidgets import QCalendarWidget, QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from ..app import AuthenticatedScreen


class CalendarScreen(AuthenticatedScreen):
    route_name = "calendar"
    route_title = "Calendar"

    def __init__(self, app_window, api):
        super().__init__(app_window, api)
        self._tasks = []
        self.status = QLabel("")
        self.status.setObjectName("Muted")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        page_wrap = QWidget()
        scroll.setWidget(page_wrap)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.selectionChanged.connect(self._render_for_selected)

        self.tasks_panel = QFrame()
        self.tasks_panel.setObjectName("Card")
        self.tasks_layout = QVBoxLayout()
        self.tasks_layout.setContentsMargins(14, 14, 14, 14)
        self.tasks_layout.setSpacing(10)
        self.tasks_panel.setLayout(self.tasks_layout)

        split = QHBoxLayout()
        split.setSpacing(14)
        split.addWidget(self.calendar, 2)
        split.addWidget(self.tasks_panel, 3)

        page = QVBoxLayout()
        page.setContentsMargins(20, 20, 20, 20)
        page.setSpacing(12)
        page.addWidget(self.status)
        page.addLayout(split, 1)
        page_wrap.setLayout(page)

        self.build_shell("calendar", "Calendar", scroll)

        self._fmt_default = QTextCharFormat()
        self._fmt_default.setForeground(QColor("#344054"))
        self._fmt_overdue = QTextCharFormat()
        self._fmt_overdue.setForeground(QColor("#DC2626"))
        self._fmt_high = QTextCharFormat()
        self._fmt_high.setForeground(QColor("#EA580C"))
        self._fmt_done = QTextCharFormat()
        self._fmt_done.setForeground(QColor("#16A34A"))

    def on_show(self):
        super().on_show()
        if not self.app_window.ensure_logged_in():
            self.app_window.navigate("login")
            return
        self.refresh()

    def refresh(self):
        res = self.api.call("tasks.list", {})
        if res.get("status") != "success":
            self.status.setText(res.get("message", "Failed to load tasks"))
            return
        self._tasks = res.get("data", {}).get("tasks", [])
        self._apply_highlights()
        self._render_for_selected()

    def _render_for_selected(self):
        while self.tasks_layout.count():
            item = self.tasks_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        selected = self.calendar.selectedDate().toString("yyyy-MM-dd")
        matching = [t for t in self._tasks if str(t.get("due_date")) == selected]
        if not matching:
            empty = QLabel("No tasks for selected date.")
            empty.setObjectName("Muted")
            self.tasks_layout.addWidget(empty)
        for task in matching:
            self.tasks_layout.addWidget(self._task_card(task))
        self.tasks_layout.addStretch(1)
        self.status.setText(f"{selected}: {len(matching)} task(s)")

    def _task_card(self, task: dict) -> QFrame:
        card = QFrame()
        card.setObjectName("TaskListCard")
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)
        title = QLabel(task.get("title", "Untitled"))
        title.setStyleSheet("font-weight: 700;")
        meta = QLabel(f"Priority: {task.get('priority', 'normal')} | Status: {task.get('status', 'backlog')}")
        meta.setObjectName("Muted")
        indicator = QLabel()
        indicator.setFixedHeight(4)
        if task.get("status") == "completed":
            indicator.setStyleSheet("background:#16A34A; border-radius: 2px;")
        elif task.get("overdue"):
            indicator.setStyleSheet("background:#DC2626; border-radius: 2px;")
        elif str(task.get("priority", "")).lower() in ("high", "urgent"):
            indicator.setStyleSheet("background:#EA580C; border-radius: 2px;")
        else:
            indicator.setStyleSheet("background:#94A3B8; border-radius: 2px;")
        layout.addWidget(indicator)
        layout.addWidget(title)
        layout.addWidget(meta)
        card.setLayout(layout)
        return card

    def _apply_highlights(self):
        self.calendar.setDateTextFormat(QDate(), self._fmt_default)
        for task in self._tasks:
            due = task.get("due_date")
            if not due:
                continue
            try:
                y, m, d = [int(p) for p in str(due).split("-")]
                qd = QDate(y, m, d)
                if task.get("status") == "completed":
                    fmt = self._fmt_done
                elif task.get("overdue"):
                    fmt = self._fmt_overdue
                elif str(task.get("priority", "")).lower() in ("high", "urgent"):
                    fmt = self._fmt_high
                else:
                    fmt = self._fmt_default
                self.calendar.setDateTextFormat(qd, fmt)
            except Exception:
                continue
