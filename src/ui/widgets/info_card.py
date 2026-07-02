from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
)

from theme import (
    BORDER,
    CARD,
    CARD_HEIGHT,
    CARD_RADIUS,
    TEXT,
    TEXT_SECONDARY,
)


class InfoCard(QFrame):

    def __init__(self, title: str, value: str):
        super().__init__()

        self.setMinimumHeight(CARD_HEIGHT)

        self.setStyleSheet(f"""
            QFrame {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: {CARD_RADIUS}px;
            }}
        """)

        layout = QVBoxLayout(self)

        self.title = QLabel(title)
        self.title.setAlignment(Qt.AlignCenter)

        self.title.setStyleSheet(f"""
            color: {TEXT_SECONDARY};
            font-size: 14px;
        """)

        self.value = QLabel(value)
        self.value.setAlignment(Qt.AlignCenter)

        self.value.setStyleSheet(f"""
            color: {TEXT};
            font-size: 34px;
            font-weight: bold;
        """)

        layout.addWidget(self.title)
        layout.addStretch()
        layout.addWidget(self.value)
        layout.addStretch()