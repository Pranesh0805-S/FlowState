from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QPushButton


class NavBar(QFrame):
    def __init__(self, app_window, title: str = ""):
        super().__init__()
        self.app_window = app_window
        self.setObjectName("TopNavBar")
        self.setFixedHeight(70)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(16, 24, 40, 28))
        self.setGraphicsEffect(shadow)

        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("TopNavTitle")

        self.notify_btn = QPushButton("🔔")
        self.notify_btn.setObjectName("TopIconBtn")
        self.notify_btn.setCursor(Qt.PointingHandCursor)
        self.notify_btn.setFixedSize(40, 40)
        self.notify_btn.setToolTip("Notifications")

        self.avatar_btn = QPushButton("U")
        self.avatar_btn.setObjectName("TopAvatarBtn")
        self.avatar_btn.setCursor(Qt.PointingHandCursor)
        self.avatar_btn.setFixedSize(40, 40)
        self.avatar_btn.setToolTip("Profile Settings")
        self.avatar_btn.clicked.connect(lambda: self.app_window.navigate("settings"))

        layout = QHBoxLayout()
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(14)
        layout.addWidget(self.title_lbl, 0, Qt.AlignVCenter)
        layout.addStretch(1)
        layout.addWidget(self.notify_btn, 0, Qt.AlignVCenter)
        layout.addWidget(self.avatar_btn, 0, Qt.AlignVCenter)
        self.setLayout(layout)

    def set_title(self, title: str):
        self.title_lbl.setText(title)

    def update_avatar(self, name: str):
        self.avatar_btn.setText(name[0].upper() if name else "U")
