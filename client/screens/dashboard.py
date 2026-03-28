from collections import defaultdict

from PyQt5.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from ..app import AuthenticatedScreen


class DashboardScreen(AuthenticatedScreen):
    route_name = "dashboard"
    route_title = "Dashboard"

    def __init__(self, app_window, api):
        super().__init__(app_window, api)

        self.cards = {}
        self.kanban_labels = {}
        self.activity_layout = QVBoxLayout()
        self.activity_layout.setContentsMargins(0, 0, 0, 0)
        self.activity_layout.setSpacing(10)

        self.status = QLabel("")
        self.status.setObjectName("Muted")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        page_wrap = QWidget()
        scroll.setWidget(page_wrap)

        page = QVBoxLayout()
        page.setContentsMargins(22, 22, 22, 22)
        page.setSpacing(14)

        stats = QGridLayout()
        stats.setHorizontalSpacing(12)
        stats.setVerticalSpacing(12)
        stats.addWidget(self._metric_card("tasks_completed_today", "Completed"), 0, 0)
        stats.addWidget(self._metric_card("tasks_completed_week", "This Week"), 0, 1)
        stats.addWidget(self._metric_card("overdue_count", "Overdue"), 0, 2)
        stats.addWidget(self._metric_card("high_priority_count", "High Priority"), 0, 3)

        kanban = QFrame()
        kanban.setObjectName("Card")
        kanban_layout = QVBoxLayout()
        kanban_layout.setContentsMargins(16, 16, 16, 16)
        kanban_layout.setSpacing(10)
        kanban_title = QLabel("Kanban Preview")
        kanban_title.setObjectName("SectionHeader")
        column_row = QHBoxLayout()
        column_row.setSpacing(10)
        for key, label in [("backlog", "Backlog"), ("in_progress", "In Progress"), ("completed", "Completed")]:
            box = QFrame()
            box.setObjectName("BoardColumn")
            bl = QVBoxLayout()
            bl.setContentsMargins(12, 12, 12, 12)
            bl.setSpacing(8)
            h = QLabel(label)
            h.setStyleSheet("font-weight: 700;")
            body = QLabel("No tasks")
            body.setObjectName("Muted")
            body.setWordWrap(True)
            self.kanban_labels[key] = body
            bl.addWidget(h)
            bl.addWidget(body)
            box.setLayout(bl)
            column_row.addWidget(box, 1)
        kanban_layout.addWidget(kanban_title)
        kanban_layout.addLayout(column_row)
        kanban.setLayout(kanban_layout)

        activity = QFrame()
        activity.setObjectName("Card")
        activity_card = QVBoxLayout()
        activity_card.setContentsMargins(16, 16, 16, 16)
        activity_card.setSpacing(10)
        activity_title = QLabel("Recent Activity")
        activity_title.setObjectName("SectionHeader")
        activity_card.addWidget(activity_title)
        activity_card.addLayout(self.activity_layout)
        activity.setLayout(activity_card)

        page.addLayout(stats)
        page.addWidget(kanban)
        page.addWidget(activity)
        page.addWidget(self.status)
        page.addStretch(1)
        page_wrap.setLayout(page)

        self.build_shell("dashboard", "Dashboard", scroll)

    def _metric_card(self, key: str, title: str) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        label = QLabel(title)
        label.setObjectName("Muted")
        value = QLabel("--")
        value.setStyleSheet("font-size: 26px; font-weight: 800;")
        self.cards[key] = value
        layout.addWidget(label)
        layout.addWidget(value)
        card.setLayout(layout)
        return card

    def on_show(self):
        super().on_show()
        if not self.app_window.ensure_logged_in():
            self.app_window.navigate("login")
            return
        self.refresh()

    def refresh(self):
        metrics_res = self.api.call("dashboard.metrics", {})
        if metrics_res.get("status") != "success":
            self.status.setText(metrics_res.get("message", "Failed to load metrics"))
            return

        data = metrics_res.get("data", {})
        for key in ("tasks_completed_today", "tasks_completed_week", "overdue_count", "high_priority_count"):
            self.cards[key].setText(str(data.get(key, "--")))

        tasks_res = self.api.call("tasks.list", {})
        stage_map = defaultdict(list)
        if tasks_res.get("status") == "success":
            for task in tasks_res.get("data", {}).get("tasks", []):
                stage_map[str(task.get("status", "backlog"))].append(task)
        for key in ("backlog", "in_progress", "completed"):
            items = stage_map.get(key, [])
            preview = []
            for task in items[:3]:
                preview.append(f"• {task.get('title', '')}")
            self.kanban_labels[key].setText("\n".join(preview) if preview else "No tasks")

        while self.activity_layout.count():
            item = self.activity_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        history_res = self.api.call("history.list", {"limit": 6})
        if history_res.get("status") == "success":
            entries = history_res.get("data", {}).get("items", [])
            if not entries:
                empty = QLabel("No activity yet.")
                empty.setObjectName("Muted")
                self.activity_layout.addWidget(empty)
            for entry in entries:
                row = QFrame()
                row.setObjectName("ActivityRow")
                rl = QHBoxLayout()
                rl.setContentsMargins(10, 10, 10, 10)
                text = QLabel(f"{entry.get('title', 'Task')} • {entry.get('event', '')} • {entry.get('timestamp', '')}")
                text.setWordWrap(True)
                rl.addWidget(text)
                row.setLayout(rl)
                self.activity_layout.addWidget(row)
        else:
            fallback = QLabel("Activity feed unavailable.")
            fallback.setObjectName("Muted")
            self.activity_layout.addWidget(fallback)

        self.status.setText("")
