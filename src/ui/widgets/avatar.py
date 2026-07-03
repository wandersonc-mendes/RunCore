from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel


class Avatar(QLabel):

    def __init__(self, size=120):
        super().__init__()

        self.size = size

        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(size, size)

        self.set_placeholder()

    def set_placeholder(self):

        radius = self.size // 2

        self.setText("👤")

        self.setStyleSheet(f"""
            QLabel {{
                background: #2d2d2d;
                border: 2px solid #666;
                border-radius: {radius}px;
                font-size: {self.size // 3}px;
            }}
        """)

    def set_image(self, image_path: str):

        if not image_path:
            self.set_placeholder()
            return

        path = Path(image_path)

        if not path.exists():
            self.set_placeholder()
            return

        pixmap = QPixmap(str(path))

        if pixmap.isNull():
            self.set_placeholder()
            return

        self.setPixmap(
            pixmap.scaled(
                self.size,
                self.size,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation,
            )
        )