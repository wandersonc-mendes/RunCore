from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from ui.training.widgets.training_week_widget import (
    TrainingWeekWidget,
)


class TrainingPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("Planejamento de Treinos")
        title.setStyleSheet("""
            font-size:22px;
            font-weight:bold;
        """)

        layout.addWidget(title)

        self.week = TrainingWeekWidget()
        layout.addWidget(self.week)

        layout.addStretch()