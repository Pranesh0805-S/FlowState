from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget

from ..app import AuthenticatedScreen


class SettingsScreen(AuthenticatedScreen):
    route_name = "settings"
    route_title = "Settings"

    def __init__(self, app_window, api):
        super().__init__(app_window, api)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        page_wrap = QWidget()
        scroll.setWidget(page_wrap)

        columns = QHBoxLayout()
        columns.setSpacing(14)

        profile_card = QFrame()
        profile_card.setObjectName("Card")
        pl = QVBoxLayout()
        pl.setContentsMargins(16, 16, 16, 16)
        pl.setSpacing(10)
        avatar = QLabel("?")
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setFixedSize(96, 96)
        avatar.setObjectName("ProfileAvatar")
        self.avatar_initial = avatar
        self.display_name_lbl = QLabel("--")
        self.display_name_lbl.setStyleSheet("font-size: 18px; font-weight: 700;")
        self.display_email_lbl = QLabel("--")
        self.display_email_lbl.setObjectName("Muted")
        pl.addWidget(avatar, 0, Qt.AlignHCenter)
        pl.addWidget(self.display_name_lbl, 0, Qt.AlignHCenter)
        pl.addWidget(self.display_email_lbl, 0, Qt.AlignHCenter)
        pl.addStretch(1)
        profile_card.setLayout(pl)
        profile_card.setMinimumWidth(280)

        forms = QWidget()
        fl = QVBoxLayout()
        fl.setContentsMargins(0, 0, 0, 0)
        fl.setSpacing(12)

        name_card = QFrame()
        name_card.setObjectName("Card")
        nl = QVBoxLayout()
        nl.setContentsMargins(16, 16, 16, 16)
        nl.setSpacing(8)
        nl.addWidget(QLabel("Update Username"))
        self.name_status = QLabel("")
        self.name_status.setObjectName("Muted")
        self.new_name = QLineEdit()
        self.new_name.setPlaceholderText("New username")
        update_name_btn = QPushButton("Update Username")
        update_name_btn.setObjectName("PrimaryBtn")
        update_name_btn.setFixedHeight(40)
        update_name_btn.clicked.connect(self.update_name)
        nl.addWidget(self.name_status)
        nl.addWidget(self.new_name)
        nl.addWidget(update_name_btn)
        name_card.setLayout(nl)

        pw_card = QFrame()
        pw_card.setObjectName("Card")
        pwl = QVBoxLayout()
        pwl.setContentsMargins(16, 16, 16, 16)
        pwl.setSpacing(8)
        pwl.addWidget(QLabel("Change Password"))
        self.pw_status = QLabel("")
        self.pw_status.setObjectName("Muted")
        self.current_pw = QLineEdit()
        self.current_pw.setPlaceholderText("Current password")
        self.current_pw.setEchoMode(QLineEdit.Password)
        self.new_pw = QLineEdit()
        self.new_pw.setPlaceholderText("New password")
        self.new_pw.setEchoMode(QLineEdit.Password)
        self.confirm_pw = QLineEdit()
        self.confirm_pw.setPlaceholderText("Confirm new password")
        self.confirm_pw.setEchoMode(QLineEdit.Password)
        change_pw_btn = QPushButton("Change Password")
        change_pw_btn.setObjectName("PrimaryBtn")
        change_pw_btn.setFixedHeight(40)
        change_pw_btn.clicked.connect(self.change_password)
        pwl.addWidget(self.pw_status)
        pwl.addWidget(self.current_pw)
        pwl.addWidget(self.new_pw)
        pwl.addWidget(self.confirm_pw)
        pwl.addWidget(change_pw_btn)
        pw_card.setLayout(pwl)

        fl.addWidget(name_card)
        fl.addWidget(pw_card)
        forms.setLayout(fl)

        columns.addWidget(profile_card, 1)
        columns.addWidget(forms, 2)

        page = QVBoxLayout()
        page.setContentsMargins(20, 20, 20, 20)
        page.addLayout(columns)
        page.addStretch(1)
        page_wrap.setLayout(page)

        self.build_shell("settings", "Settings", scroll)

    def on_show(self):
        super().on_show()
        if not self.app_window.ensure_logged_in():
            self.app_window.navigate("login")
            return
        self._load_user_info()
        self.name_status.setText("")
        self.pw_status.setText("")
        self.new_name.clear()
        self.current_pw.clear()
        self.new_pw.clear()
        self.confirm_pw.clear()

    def _load_user_info(self):
        user = self.api.user or {}
        name = user.get("name", "--")
        email = user.get("email", "--")
        self.display_name_lbl.setText(name)
        self.display_email_lbl.setText(email)
        self.avatar_initial.setText(name[0].upper() if name and name != "--" else "?")

    def update_name(self):
        new_name = self.new_name.text().strip()
        if not new_name:
            self.name_status.setText("Please enter a new username.")
            return
        res = self.api.call("auth.update_profile", {"name": new_name})
        if res.get("status") != "success":
            self.name_status.setText(res.get("message", "Update failed."))
            return
        if self.api.user:
            self.api.user["name"] = new_name
        self.name_status.setText("Username updated successfully.")
        self.new_name.clear()
        self._load_user_info()
        self.app_window.navigate("settings", push_history=False)

    def change_password(self):
        current = self.current_pw.text()
        new_pw = self.new_pw.text()
        confirm = self.confirm_pw.text()
        if not current or not new_pw or not confirm:
            self.pw_status.setText("All password fields are required.")
            return
        if new_pw != confirm:
            self.pw_status.setText("New passwords do not match.")
            return
        if len(new_pw) < 6:
            self.pw_status.setText("Password must be at least 6 characters.")
            return
        res = self.api.call("auth.change_password", {"current_password": current, "new_password": new_pw})
        if res.get("status") != "success":
            self.pw_status.setText(res.get("message", "Password change failed."))
            return
        self.pw_status.setText("Password changed successfully.")
        self.current_pw.clear()
        self.new_pw.clear()
        self.confirm_pw.clear()
