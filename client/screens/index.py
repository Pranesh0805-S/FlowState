from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from ..app import BaseScreen


class IndexScreen(BaseScreen):
    route_name = "index"
    route_title = "Welcome"
    show_nav = False

    def __init__(self, app_window, api):
        super().__init__(app_window, api)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        page_wrap = QWidget()
        scroll.setWidget(page_wrap)

        root = QVBoxLayout()
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(20)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addStretch(1)

        container = QWidget()
        container.setMaximumWidth(1200)
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(18)

        hero = QFrame()
        hero.setObjectName("HeroCard")
        hero_layout = QVBoxLayout()
        hero_layout.setContentsMargins(48, 60, 48, 60)
        hero_layout.setSpacing(14)
        hero_title = QLabel("Think, plan, and track all in one place")
        hero_title.setObjectName("HeroTitle")
        hero_title.setAlignment(Qt.AlignHCenter)
        hero_subtitle = QLabel("Efficiently manage your tasks and boost productivity.")
        hero_subtitle.setObjectName("Muted")
        hero_subtitle.setAlignment(Qt.AlignHCenter)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        get_started = QPushButton("Get Started")
        get_started.setObjectName("PrimaryBtn")
        get_started.setFixedHeight(44)
        get_started.clicked.connect(lambda: self.app_window.navigate("login"))
        sign_up = QPushButton("Sign Up")
        sign_up.setObjectName("SecondaryBtn")
        sign_up.setFixedHeight(44)
        sign_up.clicked.connect(lambda: self.app_window.navigate("register"))
        btn_row.addWidget(get_started)
        btn_row.addWidget(sign_up)
        btn_row.addStretch(1)

        hero_layout.addWidget(hero_title)
        hero_layout.addWidget(hero_subtitle)
        hero_layout.addLayout(btn_row)
        hero.setLayout(hero_layout)

        workflow_header = QLabel("Workflow Overview")
        workflow_header.setObjectName("SectionHeader")
        workflow_grid = QGridLayout()
        workflow_grid.setHorizontalSpacing(14)
        workflow_grid.setVerticalSpacing(14)
        workflow_grid.addWidget(self._card("Backlog", "Collect and prioritize upcoming tasks."), 0, 0)
        workflow_grid.addWidget(self._card("In Progress", "Track active work currently in execution."), 0, 1)
        workflow_grid.addWidget(self._card("Blocked", "Identify blockers and resolve dependencies."), 0, 2)
        workflow_grid.addWidget(self._card("Completed", "Capture finished work and outcomes."), 0, 3)

        logic_header = QLabel("Automation Logic")
        logic_header.setObjectName("SectionHeader")
        logic_row = QHBoxLayout()
        logic_row.setSpacing(14)
        logic_row.addWidget(self._card("Inputs", "Task info, deadlines, category, urgency"), 1)
        logic_row.addWidget(self._arrow(), 0)
        logic_row.addWidget(self._card("System Logic", "Rules for priority and workflow updates"), 1)
        logic_row.addWidget(self._arrow(), 0)
        logic_row.addWidget(self._card("Outputs", "Kanban board, timeline, and insights"), 1)

        insights_header = QLabel("Productivity Insights")
        insights_header.setObjectName("SectionHeader")
        insight_row = QHBoxLayout()
        insight_row.setSpacing(14)
        insight_row.addWidget(self._stat_card("Tasks Today", "--"), 1)
        insight_row.addWidget(self._stat_card("Overdue", "--"), 1)
        insight_row.addWidget(self._stat_card("High Priority", "--"), 1)
        insight_row.addWidget(self._stat_card("Completion %", "--"), 1)

        container_layout.addWidget(hero)
        container_layout.addWidget(workflow_header)
        container_layout.addLayout(workflow_grid)
        container_layout.addWidget(logic_header)
        container_layout.addLayout(logic_row)
        container_layout.addWidget(insights_header)
        container_layout.addLayout(insight_row)
        container_layout.addStretch(1)
        container.setLayout(container_layout)

        row.addWidget(container, 0)
        row.addStretch(1)
        root.addLayout(row)
        page_wrap.setLayout(root)

        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self.setLayout(outer)

    def _card(self, title: str, body: str) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 15px; font-weight: 700;")
        text = QLabel(body)
        text.setObjectName("Muted")
        text.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(text)
        card.setLayout(layout)
        return card

    def _stat_card(self, title: str, value: str) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        label = QLabel(title)
        label.setObjectName("Muted")
        number = QLabel(value)
        number.setStyleSheet("font-size: 26px; font-weight: 800;")
        layout.addWidget(label)
        layout.addWidget(number)
        card.setLayout(layout)
        return card

    def _arrow(self) -> QLabel:
        arrow = QLabel("→")
        arrow.setAlignment(Qt.AlignCenter)
        arrow.setStyleSheet("font-size: 22px; color: #98A2B3;")
        return arrow
