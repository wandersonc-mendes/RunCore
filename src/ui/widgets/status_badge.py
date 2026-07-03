from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


class StatusBadge(QLabel):

    def __init__(self):
        super().__init__()

        self.setAlignment(Qt.AlignCenter)
        self.setMinimumWidth(90)
        self.setMaximumWidth(90)

        self.set_status(True)

    def set_status(self, active: bool):

        if active:

            self.setText("ATIVO")

            self.setStyleSheet("""
                QLabel {
                    background: #1E8E3E;
                    color: white;
                    font-weight: bold;
                    border-radius: 10px;
                    padding: 4px 10px;
                }
            """)

        else:

            self.setText("INATIVO")

            self.setStyleSheet("""
                QLabel {
                    background: #C62828;
                    color: white;
                    font-weight: bold;
                    border-radius: 10px;
                    padding: 4px 10px;
                }
            """)