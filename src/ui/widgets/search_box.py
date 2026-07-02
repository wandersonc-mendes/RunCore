from PySide6.QtWidgets import QLineEdit


class SearchBox(QLineEdit):

    def __init__(self):
        super().__init__()

        self.setPlaceholderText("Pesquisar atleta...")

        self.setMinimumHeight(38)

        self.setStyleSheet("""
            QLineEdit{
                background:white;
                border:1px solid #D8D8D8;
                border-radius:8px;
                padding-left:12px;
                font-size:14px;
            }

            QLineEdit:focus{
                border:2px solid #2563EB;
            }
        """)