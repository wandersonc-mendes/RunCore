from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)


class AthleteHeader(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.photo = QLabel("👤")
        self.photo.setAlignment(Qt.AlignCenter)
        self.photo.setFixedSize(120, 120)

        self.photo.setStyleSheet("""
            QLabel {
                font-size: 42px;
                border: 2px solid #777;
                border-radius: 60px;
                background: #2d2d2d;
            }
        """)

        self.name = QLabel()
        self.name.setAlignment(Qt.AlignCenter)

        self.name.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: bold;
            }
        """)

        self.subtitle = QLabel()
        self.subtitle.setAlignment(Qt.AlignCenter)

        self.subtitle.setStyleSheet("""
            QLabel {
                color: gray;
                font-size: 14px;
            }
        """)

        layout.addWidget(self.photo, alignment=Qt.AlignCenter)
        layout.addWidget(self.name)
        layout.addWidget(self.subtitle)

    def set_athlete(self, athlete):

        self.name.setText(athlete.name or "")

        status = "🟢 Ativo" if athlete.active else "🔴 Inativo"

        goal = athlete.goal or "-"

        self.subtitle.setText(f"{status}    •    {goal}")