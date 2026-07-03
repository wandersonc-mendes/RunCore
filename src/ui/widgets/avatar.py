from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


class Avatar(QLabel):

    def __init__(self, size=120):
        super().__init__()

        self.size = size

        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        self.setText("👤")

        radius = size // 2

        self.setStyleSheet(f"""
            QLabel {{
                font-size: {size // 3}px;
                border: 2px solid #777;
                border-radius: {radius}px;
                background: #2d2d2d;
            }}
        """)

    def set_placeholder(self):
        self.setText("👤")