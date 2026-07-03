from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from repositories.athlete_repository import AthleteRepository
from ui.athletes.dialogs.new_athlete_dialog import NewAthleteDialog
from ui.athletes.dialogs.new_evaluation_dialog import NewEvaluationDialog
from ui.athletes.widgets.athlete_general_tab import AthleteGeneralTab
from ui.athletes.widgets.athlete_header import AthleteHeader


class AthleteProfileDialog(QDialog):

    def __init__(self, athlete):
        super().__init__()

        self.repository = AthleteRepository()
        self.athlete = athlete

        self.setWindowTitle("Perfil do Atleta")
        self.resize(750, 650)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.header = AthleteHeader()
        layout.addWidget(self.header)

        self.tabs = QTabWidget()

        self.general_tab = AthleteGeneralTab()

        # =====================================================
        # Aba Avaliações
        # =====================================================

        self.evaluations_tab = QWidget()

        evaluations_layout = QVBoxLayout(self.evaluations_tab)
        evaluations_layout.setSpacing(15)

        top = QHBoxLayout()
        top.addStretch()

        self.btn_new_evaluation = QPushButton(
            "+ Nova Avaliação"
        )

        top.addWidget(self.btn_new_evaluation)

        evaluations_layout.addLayout(top)

        self.lbl_empty = QLabel(
            "Nenhuma avaliação cadastrada."
        )

        self.lbl_empty.setAlignment(Qt.AlignCenter)

        self.lbl_empty.setStyleSheet("""
            QLabel {
                color: gray;
                font-size: 14px;
            }
        """)

        evaluations_layout.addStretch()
        evaluations_layout.addWidget(self.lbl_empty)
        evaluations_layout.addStretch()

        # =====================================================

        self.tabs.addTab(self.general_tab, "Geral")
        self.tabs.addTab(self.evaluations_tab, "Avaliações")
        self.tabs.addTab(QWidget(), "Treinos")
        self.tabs.addTab(QWidget(), "Histórico")
        self.tabs.addTab(QWidget(), "Competições")
        self.tabs.addTab(QWidget(), "Arquivos")

        layout.addWidget(self.tabs)

        buttons = QHBoxLayout()
        buttons.addStretch()

        self.btn_edit = QPushButton("Editar")
        self.btn_close = QPushButton("Fechar")

        buttons.addWidget(self.btn_edit)
        buttons.addWidget(self.btn_close)

        layout.addLayout(buttons)

        self.btn_close.clicked.connect(self.reject)
        self.btn_edit.clicked.connect(self.edit_athlete)

        self.btn_new_evaluation.clicked.connect(
            self.new_evaluation
        )

        self.load_data()

    def load_data(self):

        self.header.set_athlete(self.athlete)
        self.general_tab.set_athlete(self.athlete)

    def edit_athlete(self):

        dialog = NewAthleteDialog(self.athlete)

        if dialog.exec():

            self.athlete = self.repository.get_by_id(
                self.athlete.id
            )

            self.load_data()

    def new_evaluation(self):

        dialog = NewEvaluationDialog(
            self.athlete
        )

        if dialog.exec():
            print("Avaliação salva")

    def keyPressEvent(self, event):

        if event.key() == Qt.Key_Escape:
            self.reject()
            return

        super().keyPressEvent(event)