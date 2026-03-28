from collections import defaultdict

from PyQt5.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..app import AuthenticatedScreen


class TeamTasksScreen(AuthenticatedScreen):
    route_name = "team_tasks"
    route_title = "Team Tasks"

    def __init__(self, app_window, api):
        super().__init__(app_window, api)
        self.status = QLabel("")
        self.status.setObjectName("Muted")
        self._team_map = []

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        page_wrap = QWidget()
        scroll.setWidget(page_wrap)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        self.teams = QComboBox()
        self.teams.currentIndexChanged.connect(self.load_team_tasks)
        self.teams.setMinimumHeight(40)
        self.team_name = QLineEdit()
        self.team_name.setPlaceholderText("New team name")
        create_team_btn = QPushButton("Create Team")
        create_team_btn.setObjectName("PrimaryBtn")
        create_team_btn.setFixedHeight(40)
        create_team_btn.clicked.connect(self.create_team)
        top_row.addWidget(self.teams, 1)
        top_row.addWidget(self.team_name, 1)
        top_row.addWidget(create_team_btn, 0)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_teams_tab(), "Teams")
        self.tabs.addTab(self._build_board_tab(), "Team Board")

        page = QVBoxLayout()
        page.setContentsMargins(20, 20, 20, 20)
        page.setSpacing(12)
        page.addLayout(top_row)
        page.addWidget(self.tabs, 1)
        page.addWidget(self.status)
        page_wrap.setLayout(page)

        self.build_shell("team_tasks", "Team Tasks", scroll)

    def _build_teams_tab(self) -> QWidget:
        tab = QWidget()
        self.teams_list_layout = QVBoxLayout()
        self.teams_list_layout.setContentsMargins(0, 0, 0, 0)
        self.teams_list_layout.setSpacing(10)
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addLayout(self.teams_list_layout)
        layout.addStretch(1)
        tab.setLayout(layout)
        return tab

    def _build_board_tab(self) -> QWidget:
        tab = QWidget()
        row = QHBoxLayout()
        row.setContentsMargins(8, 8, 8, 8)
        row.setSpacing(10)
        self.board_columns = {}
        for key, title in [("backlog", "Backlog"), ("in_progress", "In Progress"), ("blocked", "Blocked"), ("completed", "Completed")]:
            col = QFrame()
            col.setObjectName("BoardColumn")
            cl = QVBoxLayout()
            cl.setContentsMargins(10, 10, 10, 10)
            cl.setSpacing(8)
            h = QLabel(title)
            h.setStyleSheet("font-weight: 700;")
            body = QVBoxLayout()
            body.setContentsMargins(0, 0, 0, 0)
            body.setSpacing(8)
            cl.addWidget(h)
            cl.addLayout(body)
            cl.addStretch(1)
            col.setLayout(cl)
            self.board_columns[key] = body
            row.addWidget(col, 1)
        tab.setLayout(row)
        return tab

    def on_show(self):
        super().on_show()
        if not self.app_window.ensure_logged_in():
            self.app_window.navigate("login")
            return
        self.refresh()

    def refresh(self):
        self.teams.clear()
        res = self.api.call("teams.list_for_user", {})
        if res.get("status") != "success":
            self.status.setText(res.get("message", "Failed to load teams"))
            return
        teams = res.get("data", {}).get("teams", [])
        self._team_map = [(int(t["team_id"]), t["name"]) for t in teams]
        for _, name in self._team_map:
            self.teams.addItem(name)
        self._render_teams_overview()
        if self._team_map:
            self.load_team_tasks()
        self.status.setText("Teams loaded")

    def create_team(self):
        name = self.team_name.text().strip()
        if not name:
            self.status.setText("Enter a team name.")
            return
        res = self.api.call("teams.create", {"name": name})
        if res.get("status") != "success":
            self.status.setText(res.get("message", "Create team failed"))
            return
        team = res.get("data", {}).get("team", {}) or {}
        team_id = int(team.get("id", 0) or 0)
        if team_id and self.api.user and self.api.user.get("id"):
            self.api.call("teams.assign_member", {"team_id": team_id, "user_id": int(self.api.user["id"])})
        self.team_name.clear()
        self.refresh()
        self.status.setText("Team created")

    def load_team_tasks(self):
        idx = self.teams.currentIndex()
        if idx < 0 or idx >= len(self._team_map):
            return

        for layout in self.board_columns.values():
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        team_id, team_name = self._team_map[idx]
        res = self.api.call("teams.list_team_tasks", {"team_id": team_id})
        if res.get("status") != "success":
            self.status.setText(res.get("message", "Failed to load team tasks"))
            return

        tasks = res.get("data", {}).get("tasks", [])
        grouped = defaultdict(list)
        for task in tasks:
            grouped[str(task.get("status", "backlog"))].append(task)

        for status_key, layout in self.board_columns.items():
            items = grouped.get(status_key, [])
            if not items:
                empty = QLabel("No tasks")
                empty.setObjectName("Muted")
                layout.addWidget(empty)
                continue
            for task in items[:8]:
                card = QFrame()
                card.setObjectName("TaskListCard")
                cl = QVBoxLayout()
                cl.setContentsMargins(10, 10, 10, 10)
                cl.setSpacing(4)
                title = QLabel(task.get("title", "Task"))
                title.setStyleSheet("font-weight: 700;")
                meta = QLabel(f"Priority: {task.get('priority', 'normal')}")
                meta.setObjectName("Muted")
                cl.addWidget(title)
                cl.addWidget(meta)
                card.setLayout(cl)
                layout.addWidget(card)

        self.status.setText(f"{team_name}: {len(tasks)} task(s)")

    def _render_teams_overview(self):
        while self.teams_list_layout.count():
            item = self.teams_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        if not self._team_map:
            empty = QLabel("No teams available.")
            empty.setObjectName("Muted")
            self.teams_list_layout.addWidget(empty)
            return
        for _, name in self._team_map:
            card = QFrame()
            card.setObjectName("Card")
            cl = QHBoxLayout()
            cl.setContentsMargins(12, 10, 12, 10)
            cl.addWidget(QLabel(name))
            cl.addStretch(1)
            card.setLayout(cl)
            self.teams_list_layout.addWidget(card)
