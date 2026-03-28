from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from ..app import BaseScreen


class ForgotPasswordScreen(BaseScreen):
    route_name = "forgot_password"
    route_title = "Reset Password"
    show_nav = False

    def __init__(self, app_window, api):
        super().__init__(app_window, api)

        card = QFrame()
        card.setObjectName("AuthCard")
        card.setMaximumWidth(420)

        form = QVBoxLayout()
        form.setContentsMargins(24, 24, 24, 24)
        form.setSpacing(10)

        title = QLabel("Reset Password")
        title.setObjectName("SectionHeader")
        title.setAlignment(Qt.AlignHCenter)
        subtitle = QLabel("Enter your email and new password")
        subtitle.setObjectName("Muted")
        subtitle.setAlignment(Qt.AlignHCenter)

        self.status = QLabel("")
        self.status.setObjectName("Muted")
        self.status.setAlignment(Qt.AlignHCenter)
        self.status.setWordWrap(True)

        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")
        self.new_pw = QLineEdit()
        self.new_pw.setPlaceholderText("New password")
        self.new_pw.setEchoMode(QLineEdit.Password)
        self.confirm_pw = QLineEdit()
        self.confirm_pw.setPlaceholderText("Confirm password")
        self.confirm_pw.setEchoMode(QLineEdit.Password)

        reset_btn = QPushButton("Set New Password")
        reset_btn.setObjectName("GradientBtn")
        reset_btn.setFixedHeight(42)
        reset_btn.clicked.connect(self.do_reset)

        back_btn = QPushButton("Back to Login")
        back_btn.setObjectName("LinkBtn")
        back_btn.clicked.connect(lambda: self.app_window.navigate("login"))

        form.addWidget(title)
        form.addWidget(subtitle)
        form.addWidget(self.status)
        form.addWidget(self.email)
        form.addWidget(self.new_pw)
        form.addWidget(self.confirm_pw)
        form.addWidget(reset_btn)
        form.addWidget(back_btn, 0, Qt.AlignHCenter)
        card.setLayout(form)

        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.addStretch(1)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(card)
        row.addStretch(1)
        root.addLayout(row)
        root.addStretch(1)
        self.setLayout(root)

    def on_show(self):
        self.status.setText("")
        self.email.clear()
        self.new_pw.clear()
        self.confirm_pw.clear()

    def do_reset(self):
        email = self.email.text().strip()
        new_pw = self.new_pw.text()
        confirm = self.confirm_pw.text()

        if not email:
            self.status.setText("Please enter your email.")
            return
        if not new_pw or not confirm:
            self.status.setText("Please fill both password fields.")
            return
        if new_pw != confirm:
            self.status.setText("Passwords do not match.")
            return
        if len(new_pw) < 6:
            self.status.setText("Password must be at least 6 characters.")
            return

        self.status.setText("Updating password...")
        res = self.api.call("auth.reset_password", {"email": email, "new_password": new_pw})
        if res.get("status") != "success":
            self.status.setText(res.get("message", "Reset failed."))
            return
        self.status.setText("Password updated. You can log in now.")
        self.new_pw.clear()
        self.confirm_pw.clear()
