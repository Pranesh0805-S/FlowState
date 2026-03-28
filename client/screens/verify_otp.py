from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from ..app import BaseScreen


class VerifyOtpScreen(BaseScreen):
    route_name = "verify_otp"
    route_title = "Verify OTP"
    show_nav = False

    def __init__(self, app_window, api):
        super().__init__(app_window, api)

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

        title = QLabel("Verify Your Email")
        title.setAlignment(Qt.AlignHCenter)
        title.setStyleSheet("font-size: 30px; font-weight: 800;")
        subtitle = QLabel("Enter the 6-digit OTP sent to your email")
        subtitle.setObjectName("Muted")
        subtitle.setAlignment(Qt.AlignHCenter)

        self.email_lbl = QLabel("")
        self.email_lbl.setObjectName("Muted")
        self.email_lbl.setAlignment(Qt.AlignHCenter)

        self.otp_input = QLineEdit()
        self.otp_input.setPlaceholderText("6-digit OTP")
        self.otp_input.setMaxLength(6)
        self.otp_input.setFixedHeight(42)

        self.error_lbl = QLabel("")
        self.error_lbl.setVisible(False)
        self.error_lbl.setStyleSheet("color:#DC2626; font-weight:600;")
        self.success_lbl = QLabel("")
        self.success_lbl.setVisible(False)
        self.success_lbl.setStyleSheet("color:#16A34A; font-weight:600;")

        verify_btn = QPushButton("Verify")
        verify_btn.setObjectName("GradientBtn")
        verify_btn.setFixedHeight(44)
        verify_btn.clicked.connect(self.verify_otp)

        back_btn = QPushButton("Back to Register")
        back_btn.setObjectName("LinkBtn")
        back_btn.clicked.connect(lambda: self.app_window.navigate("register"))

        form.addWidget(title)
        form.addWidget(subtitle)
        form.addWidget(self.email_lbl)
        form.addWidget(self.otp_input)
        form.addWidget(self.error_lbl)
        form.addWidget(self.success_lbl)
        form.addWidget(verify_btn)
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
        email = getattr(self.app_window, "pending_verification_email", "")
        self.email_lbl.setText(email if email else "No email selected")
        self.otp_input.clear()
        self.error_lbl.setVisible(False)
        self.success_lbl.setVisible(False)

    def verify_otp(self):
        email = getattr(self.app_window, "pending_verification_email", "")
        otp = self.otp_input.text().strip()
        self.error_lbl.setVisible(False)
        self.success_lbl.setVisible(False)

        if not email:
            self.error_lbl.setText("Email missing. Please register again.")
            self.error_lbl.setVisible(True)
            return
        if len(otp) != 6 or not otp.isdigit():
            self.error_lbl.setText("Please enter a valid 6-digit OTP.")
            self.error_lbl.setVisible(True)
            return

        res = self.api.call("auth.verify_otp", {"email": email, "otp_input": otp})
        if res.get("status") != "success":
            self.error_lbl.setText(res.get("message", "Invalid OTP"))
            self.error_lbl.setVisible(True)
            return

        self.success_lbl.setText("Account Verified")
        self.success_lbl.setVisible(True)
        QTimer.singleShot(2000, lambda: self.app_window.navigate("login"))
