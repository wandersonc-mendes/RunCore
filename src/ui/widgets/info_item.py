from PySide6.QtWidgets import (
    QLabel,
    QHBoxLayout,
    QWidget,
)

from theme import TEXT, TEXT_SECONDARY


class InfoItem(QWidget):

    def __init__(self, title: str, value: str = "-"):
        super().__init__()

        layout = QHBoxLayout(self)

        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)

        self.title = QLabel(title.upper())

        self.title.setMinimumWidth(110)

        self.title.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
        """)

        self.value = QLabel(value)

        self.value.setWordWrap(True)

        self.default_style = f"""
            QLabel {{
                color: {TEXT};
                font-size: 14px;
            }}
        """

        self.value.setStyleSheet(self.default_style)

        layout.addWidget(self.title)
        layout.addWidget(self.value, 1)

    def set_value(self, value):

        if value in (None, ""):
            value = "-"

        self.value.setText(str(value))
        self.value.setStyleSheet(self.default_style)

    def set_colored_value(self, value, color):

        if value in (None, ""):
            value = "-"

        self.value.setText(str(value))

        self.value.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 14px;
                font-weight: bold;
            }}
        """)