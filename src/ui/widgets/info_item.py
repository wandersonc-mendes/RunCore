from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout


class InfoItem(QWidget):

    def __init__(self, title: str, value: str = "-"):
        super().__init__()

        layout = QHBoxLayout(self)

        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(10)

        self.title = QLabel(title)

        self.title.setMinimumWidth(120)

        self.title.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #666;
            }
        """)

        self.value = QLabel(value)

        self.value.setStyleSheet("""
            QLabel {
                color: #222;
            }
        """)

        layout.addWidget(self.title)
        layout.addWidget(self.value)
        layout.addStretch()

    def set_value(self, value):

        if value is None or value == "":
            value = "-"

        self.value.setText(str(value))