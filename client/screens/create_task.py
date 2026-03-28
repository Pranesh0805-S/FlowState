from datetime import date

from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..app import AuthenticatedScreen


class CreateTaskScreen(AuthenticatedScreen):
    route_name = "create_task"
    route_title = "Create Task"

    def __init__(self, app_window, api):
        super().__init__(app_window, api)

        self.status = QLabel("")
        self.status.setObjectName("Muted")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        wrap = QWidget()
        scroll.setWidget(wrap)

        card = QFrame()
        card.setObjectName("Card")
        card.setMaximumWidth(500)

        form = QVBoxLayout()
        form.setContentsMargins(22, 22, 22, 22)
        form.setSpacing(12)

        head = QLabel("Create Task")
        head.setObjectName("SectionHeader")
        self.title_in = QLineEdit()
        self.title_in.setPlaceholderText("Task title")
        self.desc_in = QTextEdit()
        self.desc_in.setPlaceholderText("Task description")
        self.desc_in.setFixedHeight(110)

        self.category = QLineEdit()
        self.category.setPlaceholderText("Category")
        self.status_combo = QComboBox()
        self.status_combo.addItems(["backlog", "in_progress", "blocked", "completed"])

        row1 = QHBoxLayout()
        row1.setSpacing(10)
        row1.addWidget(self._field("Category", self.category), 1)
        row1.addWidget(self._field("Status", self.status_combo), 1)

        self.due = QDateEdit()
        self.due.setCalendarPopup(True)
        self.due.setDate(date.today())
        self.estimated = QSpinBox()
        self.estimated.setRange(0, 24 * 60)
        self.estimated.setValue(30)
        self.estimated.setSuffix(" min")

        row2 = QHBoxLayout()
        row2.setSpacing(10)
        row2.addWidget(self._field("Due Date", self.due), 1)
        row2.addWidget(self._field("Time Estimate", self.estimated), 1)

        self.urgent = QCheckBox("Urgent")
        create_btn = QPushButton("Create Task")
        create_btn.setObjectName("PrimaryBtn")
        create_btn.setFixedHeight(42)
        create_btn.clicked.connect(self.create_task)

        form.addWidget(head)
        form.addWidget(self.status)
        form.addWidget(self._field("Title", self.title_in))
        form.addWidget(self._field("Description", self.desc_in))
        form.addLayout(row1)
        form.addLayout(row2)
        form.addWidget(self.urgent)
        form.addWidget(create_btn)
        card.setLayout(form)

        page = QVBoxLayout()
        page.addStretch(1)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(card)
        row.addStretch(1)
        page.addLayout(row)
        page.addStretch(1)
        wrap.setLayout(page)

        self.build_shell("create_task", "Create Task", scroll)

    def on_show(self):
        super().on_show()
        if not self.app_window.ensure_logged_in():
            self.app_window.navigate("login")
            return
        self.status.setText("")

    def create_task(self):
        payload = {
            "title": self.title_in.text().strip(),
            "description": self.desc_in.toPlainText().strip(),
            "category": self.category.text().strip(),
            "status": self.status_combo.currentText(),
            "due_date": self.due.date().toString("yyyy-MM-dd"),
            "duration_estimated": int(self.estimated.value()),
            "urgency_flag": bool(self.urgent.isChecked()),
        }
        res = self.api.call("tasks.create", payload)
        if res.get("status") != "success":
            self.status.setText(res.get("message", "Create failed"))
            return
        self.status.setText("Task created successfully.")
        self.title_in.clear()
        self.desc_in.clear()
        self.category.clear()
        self.urgent.setChecked(False)

    def _field(self, label: str, widget: QWidget) -> QWidget:
        wrap = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        caption = QLabel(label)
        caption.setObjectName("Muted")
        layout.addWidget(caption)
        layout.addWidget(widget)
        wrap.setLayout(layout)
        return wrap
