from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from repositories.athlete_repository import AthleteRepository


class NewAthleteDialog(QDialog):

    def __init__(self, athlete=None):
        super().__init__()

        self.repository = AthleteRepository()
        self.athlete = athlete

        self.setWindowTitle(
            "Editar Atleta" if athlete else "Novo Atleta"
        )

        self.resize(520, 520)

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.name = QLineEdit()
        self.phone = QLineEdit()
        self.email = QLineEdit()

        self.goal = QComboBox()
        self.goal.addItems([
            "5 km",
            "10 km",
            "21 km",
            "42 km",
            "Trail",
            "Outro",
        ])

        self.status = QComboBox()
        self.status.addItems([
            "Ativo",
            "Inativo",
        ])

        self.notes = QTextEdit()

        form.addRow("Nome *", self.name)
        form.addRow("Telefone", self.phone)
        form.addRow("E-mail", self.email)
        form.addRow("Objetivo", self.goal)
        form.addRow("Status", self.status)
        form.addRow("Observações", self.notes)

        layout.addLayout(form)

        botoes = QHBoxLayout()

        self.save = QPushButton("Salvar")
        self.cancel = QPushButton("Cancelar")

        botoes.addStretch()
        botoes.addWidget(self.save)
        botoes.addWidget(self.cancel)

        layout.addLayout(botoes)

        self.cancel.clicked.connect(self.reject)
        self.save.clicked.connect(self.save_athlete)

        self.cancel.setAutoDefault(False)
        self.cancel.setDefault(False)

        self.save.setAutoDefault(True)
        self.save.setDefault(True)

        if self.athlete:
            self.load_data()
        self.name.setFocus()
        self.name.selectAll()
    def load_data(self):

        self.name.setText(self.athlete.name)
        self.phone.setText(self.athlete.phone)
        self.email.setText(self.athlete.email)
        self.notes.setPlainText(self.athlete.notes)

        self.goal.setCurrentText(self.athlete.goal)

        self.status.setCurrentText(
            "Ativo" if self.athlete.active else "Inativo"
        )

    def save_athlete(self):

        if self.name.text().strip() == "":

            QMessageBox.warning(
                self,
                "Atenção",
                "Informe o nome do atleta.",
            )

            return

        if self.athlete is None:

            self.repository.create(
                name=self.name.text(),
                phone=self.phone.text(),
                email=self.email.text(),
                goal=self.goal.currentText(),
                active=self.status.currentText() == "Ativo",
                notes=self.notes.toPlainText(),
            )

        else:

            self.repository.update(
                athlete_id=self.athlete.id,
                name=self.name.text(),
                phone=self.phone.text(),
                email=self.email.text(),
                goal=self.goal.currentText(),
                active=self.status.currentText() == "Ativo",
                notes=self.notes.toPlainText(),
            )

        self.accept()