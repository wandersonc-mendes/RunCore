from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton


class SidebarButton(QPushButton):

    def __init__(self, text):
        super().__init__(text)

        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(45)

        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                border: none;
                text-align: left;
                padding-left: 18px;
                font-size: 14px;
            }

            QPushButton:hover {
                background: #2d333b;
            }

            QPushButton:pressed {
                background: #3b82f6;
            }
        """)