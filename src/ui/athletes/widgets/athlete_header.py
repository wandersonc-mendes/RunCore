from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ui.widgets.avatar import Avatar
from ui.widgets.status_badge import StatusBadge


class AthleteHeader(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.avatar = Avatar(120)

        self.name = QLabel()
        self.name.setAlignment(Qt.AlignCenter)

        self.name.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
            }
        """)

        info_layout = QHBoxLayout()
        info_layout.setAlignment(Qt.AlignCenter)
        info_layout.setSpacing(12)

        self.status = StatusBadge()

        self.goal = QLabel()

        self.goal.setStyleSheet("""
            QLabel {
                color: gray;
                font-size: 14px;
                font-weight: 500;
            }
        """)

        info_layout.addWidget(self.status)
        info_layout.addWidget(self.goal)

        layout.addWidget(
            self.avatar,
            alignment=Qt.AlignCenter,
        )

        layout.addWidget(self.name)
        layout.addLayout(info_layout)

    def set_athlete(self, athlete):

        self.name.setText(athlete.name or "")

        self.status.set_status(athlete.active)

        self.goal.setText(
            f"🎯 {athlete.goal or '-'}"
        )

        if hasattr(athlete, "photo"):
            self.avatar.set_image(athlete.photo)
        else:
            self.avatar.set_placeholder()