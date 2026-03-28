from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class KanbanColumn(QFrame):
    taskDropped = pyqtSignal(int, str)

    def __init__(self, status_key: str, title: str):
        super().__init__()
        self.status_key = status_key
        self.setObjectName("KanbanColumn")
        self.setAcceptDrops(True)

        self.header = QLabel(title)
        self.header.setObjectName("KanbanColumnTitle")

        self.cards_wrap = QWidget()
        self.cards_layout = QVBoxLayout()
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        self.cards_wrap.setLayout(self.cards_layout)

        self.empty = QLabel("Drop tasks here")
        self.empty.setObjectName("Muted")

        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        layout.addWidget(self.header)
        layout.addWidget(self.empty)
        layout.addWidget(self.cards_wrap, 1)
        self.setLayout(layout)

    def clear_cards(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._sync_empty()

    def add_card(self, card: QWidget):
        card.setParent(self.cards_wrap)
        self.cards_layout.addWidget(card)
        self._sync_empty()

    def _sync_empty(self):
        self.empty.setVisible(self.cards_layout.count() == 0)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event):
        if not event.mimeData().hasText():
            event.ignore()
            return
        try:
            task_id = int(event.mimeData().text())
        except Exception:
            event.ignore()
            return
        self.taskDropped.emit(task_id, self.status_key)
        event.acceptProposedAction()
