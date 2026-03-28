from typing import Dict, List

from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QScrollArea,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from ..app import AuthenticatedScreen
from ..widgets.task_card import TaskCard


STATUS_LABELS = [
    ("backlog", "Backlog"),
    ("in_progress", "In Progress"),
    ("blocked", "Blocked"),
    ("completed", "Completed"),
]


class WorkflowScreen(AuthenticatedScreen):
    route_name = "workflow"
    route_title = "Workflow Board"

    def __init__(self, app_window, api):
        super().__init__(app_window, api)
        self.status = QLabel("")
        self.status.setObjectName("Muted")
        self.stage_items: Dict[str, List[dict]] = {k: [] for k, _ in STATUS_LABELS}
        self.columns: Dict[str, QVBoxLayout] = {}

        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.tray.setVisible(True)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        page_wrap = QWidget()
        scroll.setWidget(page_wrap)

        page = QVBoxLayout()
        page.setContentsMargins(20, 20, 20, 20)
        page.setSpacing(14)

        desc = QLabel("Use Move Left/Move Right on each task card.")
        desc.setObjectName("Muted")

        board = QFrame()
        board.setObjectName("BoardFrame")
        board_row = QHBoxLayout()
        board_row.setContentsMargins(0, 0, 0, 0)
        board_row.setSpacing(12)

        for key, title in STATUS_LABELS:
            col = QFrame()
            col.setObjectName("KanbanColumn")
            col_layout = QVBoxLayout()
            col_layout.setContentsMargins(12, 12, 12, 12)
            col_layout.setSpacing(15)
            head = QLabel(title)
            head.setObjectName("SectionHeader")
            list_wrap = QVBoxLayout()
            list_wrap.setContentsMargins(0, 0, 0, 0)
            list_wrap.setSpacing(15)
            col_layout.addWidget(head)
            col_layout.addLayout(list_wrap)
            col_layout.addStretch(1)
            col.setLayout(col_layout)
            self.columns[key] = list_wrap
            board_row.addWidget(col, 1)
        board.setLayout(board_row)

        page.addWidget(desc)
        page.addWidget(board, 1)
        page.addWidget(self.status)
        page_wrap.setLayout(page)

        self.build_shell("workflow", "Workflow", scroll)

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

        self.stage_items = {k: [] for k, _ in STATUS_LABELS}
        for task in res.get("data", {}).get("tasks", []):
            status_key = str(task.get("status", "backlog"))
            if status_key not in self.stage_items:
                status_key = "backlog"
            self.stage_items[status_key].append(task)

        for status_key, layout in self.columns.items():
            self._clear_layout(layout)
            tasks = self.stage_items.get(status_key, [])
            if not tasks:
                empty = QLabel("No tasks")
                empty.setObjectName("Muted")
                layout.addWidget(empty)
                continue
            for task in tasks:
                card = TaskCard(task)
                card.moveRequested.connect(self._on_move_requested)
                layout.addWidget(card)

        self.status.setText("")

    def _on_move_requested(self, task_id: int, direction: int):
        task = self._find_task(task_id)
        if not task:
            self.status.setText("Task not found.")
            self.refresh()
            return

        keys = [k for k, _ in STATUS_LABELS]
        current_status = str(task.get("status", "backlog"))
        if current_status not in keys:
            current_status = "backlog"
        idx = keys.index(current_status)
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(keys):
            self.status.setText("Cannot move further in that direction.")
            return
        new_status = keys[new_idx]

        reply = QMessageBox.question(
            self,
            "Confirm Move",
            "Do you want to move this task?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            self.status.setText("Move cancelled.")
            return

        self._move_task(int(task.get("id")), new_status)

    def _move_task(self, task_id: int, new_status: str):
        res = self.api.call("tasks.move", {"task_id": task_id, "status": new_status})
        if res.get("status") != "success":
            self.status.setText(res.get("message", "Move failed"))
            return

        self.status.setText("Task moved successfully.")
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.showMessage("Task Update", "Task moved successfully", QSystemTrayIcon.Information, 1800)
        self.refresh()

    def _find_task(self, task_id: int):
        for tasks in self.stage_items.values():
            for task in tasks:
                if int(task.get("id", -1)) == task_id:
                    return task
        return None

    def _clear_layout(self, layout: QVBoxLayout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
