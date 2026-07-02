from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

from theme import PRIMARY


class PrimaryButton(QPushButton):

    def __init__(self, text: str):
        super().__init__(text)

        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(42)

        self.setStyleSheet(f"""
            QPushButton {{
                background:{PRIMARY};
                color:white;
                border:none;
                border-radius:8px;
                font-size:14px;
                font-weight:bold;
                padding:8px 18px;
            }}

            QPushButton:hover {{
                background:#1d4ed8;
            }}

            QPushButton:pressed {{
                background:#1e40af;
            }}
        """)