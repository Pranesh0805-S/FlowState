from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from ..app import BaseScreen


class LoginScreen(BaseScreen):
    route_name = "login"
    route_title = "Login"
    show_nav = False

    def __init__(self, app_window, api):
        super().__init__(app_window, api)
        self.setObjectName("AuthPage")

        card = QFrame()
        card.setObjectName("AuthCard")
        card.setMinimumWidth(420)
        card.setMaximumWidth(460)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)

        form = QVBoxLayout()
        form.setContentsMargins(28, 28, 28, 28)
        form.setSpacing(12)

        title = QLabel("Welcome Back")
        title.setAlignment(Qt.AlignHCenter)
        title.setStyleSheet("font-size: 30px; font-weight: 800;")
        subtitle = QLabel("Sign in to continue")
        subtitle.setObjectName("Muted")
        subtitle.setAlignment(Qt.AlignHCenter)

        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)
        self.email.textChanged.connect(self._clear_error_state)
        self.password.textChanged.connect(self._clear_error_state)

        self.error_lbl = QLabel("")
        self.error_lbl.setVisible(False)
        self.error_lbl.setStyleSheet("color: #DC2626; font-weight: 600;")

        login_btn = QPushButton("Sign In")
        login_btn.setObjectName("GradientBtn")
        login_btn.setFixedHeight(44)
        login_btn.clicked.connect(self.do_login)

        forgot = QPushButton("Forgot password?")
        forgot.setObjectName("LinkBtn")
        forgot.clicked.connect(lambda: self.app_window.navigate("forgot_password"))

        signup = QPushButton("Create an account")
        signup.setObjectName("LinkBtn")
        signup.clicked.connect(lambda: self.app_window.navigate("register"))

        form.addWidget(title)
        form.addWidget(subtitle)
        form.addWidget(self.email)
        form.addWidget(self.password)
        form.addWidget(self.error_lbl)
        form.addWidget(login_btn)
        form.addWidget(forgot, 0, Qt.AlignRight)
        form.addWidget(signup, 0, Qt.AlignHCenter)
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

    def do_login(self):
        res = self.api.call("auth.login", {"email": self.email.text().strip(), "password": self.password.text()})
        if res.get("status") != "success":
            self._set_error_state("Invalid credentials")
            return
        self._clear_error_state()
        data = res.get("data", {})
        self.api.set_auth(data.get("token"), data.get("user"))
        self.app_window.navigate("dashboard")

    def _set_error_state(self, message: str):
        self.error_lbl.setText(message)
        self.error_lbl.setVisible(True)
        error_style = "border: 1px solid #DC2626;"
        self.email.setStyleSheet(error_style)
        self.password.setStyleSheet(error_style)

    def _clear_error_state(self, *_):
        self.error_lbl.setVisible(False)
        self.error_lbl.setText("")
        self.email.setStyleSheet("")
        self.password.setStyleSheet("")
