from PySide6.QtWidgets import (
    QHBoxLayout,
    QWidget,
)

from ui.widgets.primary_button import PrimaryButton
from ui.widgets.search_box import SearchBox


class AthletesToolbar(QWidget):

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)

        self.search = SearchBox()

        self.btn_new = PrimaryButton("+ Novo Atleta")
        self.btn_delete = PrimaryButton("🗑 Excluir")

        layout.addWidget(self.search)
        layout.addWidget(self.btn_new)
        layout.addWidget(self.btn_delete)

        layout.setContentsMargins(0, 0, 0, 0)