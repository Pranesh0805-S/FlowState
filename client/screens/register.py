from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..app import BaseScreen


class RegisterScreen(BaseScreen):
    route_name = "register"
    route_title = "Register"
    show_nav = False

    def __init__(self, app_window, api):
        super().__init__(app_window, api)
        self.setObjectName("AuthPage")
        self.pending_name = ""
        self.pending_email = ""

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
        form.setSpacing(14)

        title = QLabel("Create Account")
        title.setAlignment(Qt.AlignHCenter)
        title.setStyleSheet("font-size: 30px; font-weight: 800;")
        subtitle = QLabel("Start managing your work in one place")
        subtitle.setObjectName("Muted")
        subtitle.setAlignment(Qt.AlignHCenter)

        self.status = QLabel("")
        self.status.setVisible(False)

        self.steps = QStackedWidget()
        self.step1 = self._build_step1()
        self.step2 = self._build_step2()
        self.steps.addWidget(self.step1)
        self.steps.addWidget(self.step2)

        login_link = QPushButton("Already have an account? Login")
        login_link.setObjectName("LinkBtn")
        login_link.clicked.connect(lambda: self.app_window.navigate("login"))

        form.addWidget(title)
        form.addWidget(subtitle)
        form.addWidget(self.status)
        form.addWidget(self.steps)
        form.addWidget(login_link, 0, Qt.AlignHCenter)
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

    def _build_step1(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.name = QLineEdit()
        self.name.setPlaceholderText("Full Name")
        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")

        self.send_otp_btn = QPushButton("Send OTP")
        self.send_otp_btn.setObjectName("GradientBtn")
        self.send_otp_btn.setFixedHeight(42)
        self.send_otp_btn.clicked.connect(self.send_otp)

        self.otp_input = QLineEdit()
        self.otp_input.setPlaceholderText("Enter OTP")
        self.otp_input.setMaxLength(6)
        self.otp_input.setEnabled(False)

        self.verify_otp_btn = QPushButton("Verify OTP")
        self.verify_otp_btn.setObjectName("GradientBtn")
        self.verify_otp_btn.setFixedHeight(42)
        self.verify_otp_btn.setEnabled(False)
        self.verify_otp_btn.clicked.connect(self.verify_otp)

        layout.addWidget(self.name)
        layout.addWidget(self.email)
        layout.addWidget(self.send_otp_btn)
        layout.addWidget(self.otp_input)
        layout.addWidget(self.verify_otp_btn)
        page.setLayout(layout)
        return page

    def _build_step2(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)
        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText("Confirm Password")
        self.confirm_password.setEchoMode(QLineEdit.Password)

        self.register_btn = QPushButton("Register")
        self.register_btn.setObjectName("GradientBtn")
        self.register_btn.setFixedHeight(42)
        self.register_btn.clicked.connect(self.complete_registration)

        layout.addWidget(self.password)
        layout.addWidget(self.confirm_password)
        layout.addWidget(self.register_btn)
        page.setLayout(layout)
        return page

    def on_show(self):
        self.steps.setCurrentIndex(0)
        self.pending_name = ""
        self.pending_email = ""
        self.name.clear()
        self.email.clear()
        self.otp_input.clear()
        self.otp_input.setEnabled(False)
        self.verify_otp_btn.setEnabled(False)
        self.password.clear()
        self.confirm_password.clear()
        self._set_status("")

    def _set_status(self, message: str, success: bool = False):
        if not message:
            self.status.setText("")
            self.status.setVisible(False)
            return
        self.status.setStyleSheet("color:#16A34A; font-weight:600;" if success else "color:#DC2626; font-weight:600;")
        self.status.setText(message)
        self.status.setVisible(True)

    def _set_step1_busy(self, busy: bool):
        self.send_otp_btn.setEnabled(not busy)
        self.verify_otp_btn.setEnabled((not busy) and self.otp_input.isEnabled())

    def _set_step2_busy(self, busy: bool):
        self.register_btn.setEnabled(not busy)

    def send_otp(self):
        name = self.name.text().strip()
        email = self.email.text().strip().lower()
        self._set_status("")
        if not name or not email:
            self._set_status("Name and email are required")
            return

        self._set_step1_busy(True)
        res = self.api.call("auth.send_registration_otp", {"name": name, "email": email})
        self._set_step1_busy(False)

        if res.get("status") != "success":
            self._set_status(res.get("message", "Failed to send OTP"))
            return

        self.pending_name = name
        self.pending_email = email
        self.otp_input.setEnabled(True)
        self.verify_otp_btn.setEnabled(True)
        self._set_status("OTP sent successfully", success=True)

    def verify_otp(self):
        email = self.pending_email or self.email.text().strip().lower()
        otp = self.otp_input.text().strip()
        self._set_status("")

        if not email:
            self._set_status("Email is required")
            return
        if len(otp) != 6 or not otp.isdigit():
            self._set_status("Invalid OTP")
            return

        self._set_step1_busy(True)
        res = self.api.call("auth.verify_registration_otp", {"email": email, "otp": otp})
        self._set_step1_busy(False)

        if res.get("status") != "success":
            self._set_status(res.get("message", "Invalid OTP"))
            return

        self.pending_email = email
        self.steps.setCurrentWidget(self.step2)
        self._set_status("")

    def complete_registration(self):
        password = self.password.text()
        confirm_password = self.confirm_password.text()
        self._set_status("")

        if len(password) < 8:
            self._set_status("Password must be at least 8 characters")
            return
        if password != confirm_password:
            self._set_status("Passwords do not match")
            return
        if not self.pending_email:
            self._set_status("OTP verification required")
            self.steps.setCurrentWidget(self.step1)
            return

        self._set_step2_busy(True)
        res = self.api.call("auth.complete_registration", {"email": self.pending_email, "password": password})
        self._set_step2_busy(False)

        if res.get("status") != "success":
            self._set_status(res.get("message", "Registration failed"))
            return

        login_res = self.api.call("auth.login", {"email": self.pending_email, "password": password})
        if login_res.get("status") != "success":
            self._set_status("Successfully Registered", success=True)
            self.app_window.navigate("login")
            return

        data = login_res.get("data", {})
        self.api.set_auth(data.get("token"), data.get("user"))
        self._set_status("Successfully Registered", success=True)
        self.app_window.navigate("dashboard")
