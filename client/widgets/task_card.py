from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout


class TaskCard(QFrame):
    moveRequested = pyqtSignal(int, int)  # task_id, direction (-1 left / +1 right)

    def __init__(self, task: dict):
        super().__init__()
        self.task = task
        self.setObjectName("KanbanTaskCard")
        self.setMinimumHeight(170)
        self.setMaximumHeight(170)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        title = QLabel(task.get("title", "Untitled Task"))
        title.setObjectName("TaskCardTitle")
        title.setWordWrap(True)

        due_text = task.get("due_date") or "No due date"
        due = QLabel(f"Due: {due_text}")
        due.setObjectName("TaskCardMeta")

        priority = str(task.get("priority", "normal")).capitalize()
        badge = QLabel(priority)
        badge.setObjectName("TaskPriorityBadge")

        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        meta_row.setSpacing(8)
        meta_row.addWidget(due)
        meta_row.addStretch(1)
        meta_row.addWidget(badge)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(8)
        left_btn = QPushButton("Move Left")
        right_btn = QPushButton("Move Right")
        left_btn.setObjectName("SecondaryBtn")
        right_btn.setObjectName("PrimaryBtn")
        left_btn.setFixedHeight(32)
        right_btn.setFixedHeight(32)
        left_btn.clicked.connect(lambda: self.moveRequested.emit(int(self.task.get("id", -1)), -1))
        right_btn.clicked.connect(lambda: self.moveRequested.emit(int(self.task.get("id", -1)), +1))
        actions.addWidget(left_btn, 1)
        actions.addWidget(right_btn, 1)

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        layout.addWidget(title)
        layout.addLayout(meta_row)
        layout.addStretch(1)
        layout.addLayout(actions)
        self.setLayout(layout)

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setOffset(0, 2)
        self._shadow.setBlurRadius(14)
        self._shadow.setColor(QColor(15, 23, 42, 20))
        self.setGraphicsEffect(self._shadow)

    def enterEvent(self, event):
        self._shadow.setColor(QColor(15, 23, 42, 38))
        self._shadow.setBlurRadius(22)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._shadow.setColor(QColor(15, 23, 42, 20))
        self._shadow.setBlurRadius(14)
        super().leaveEvent(event)
