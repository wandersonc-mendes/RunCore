from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from theme import (
    BORDER,
    CARD,
    CARD_RADIUS,
    TEXT,
)


class SectionCard(QFrame):

    def __init__(self, title: str):
        super().__init__()

        self.setStyleSheet(f"""
            QFrame {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: {CARD_RADIUS}px;
            }}

            QLabel {{
                border: none;
            }}
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(18, 18, 18, 18)
        self.main_layout.setSpacing(15)

        self.title = QLabel(title)

        self.title.setStyleSheet(f"""
            color: {TEXT};
            font-size: 16px;
            font-weight: bold;
        """)

        self.main_layout.addWidget(self.title)

        self.content = QWidget()

        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)

        self.main_layout.addWidget(self.content)

    def add_widget(self, widget):
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        self.content_layout.addLayout(layout)

    def add_spacing(self, value=8):
        self.content_layout.addSpacing(value)

    def add_stretch(self):
        self.content_layout.addStretch()