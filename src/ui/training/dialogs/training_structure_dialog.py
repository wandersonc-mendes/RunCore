from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class TrainingStructureDialog(QDialog):

    def __init__(self, steps=None):
        super().__init__()

        self.setWindowTitle("Estrutura do Treino")
        self.resize(900, 650)

        self.steps = list(steps) if steps else []

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.cmb_type = QComboBox()
        self.cmb_type.addItems([
            "Aquecimento",
            "Corrida",
            "Intervalado",
            "Desaquecimento",
            "Caminhada",
        ])

        self.edt_distance = QDoubleSpinBox()
        self.edt_distance.setDecimals(3)
        self.edt_distance.setRange(0, 100)

        self.edt_repetitions = QSpinBox()
        self.edt_repetitions.setRange(0, 100)

        self.edt_pace_min = QLineEdit()
        self.edt_pace_max = QLineEdit()
        self.edt_notes = QLineEdit()

        form.addRow("Tipo", self.cmb_type)
        form.addRow("Distância", self.edt_distance)
        form.addRow("Repetições", self.edt_repetitions)
        form.addRow("Pace Inicial", self.edt_pace_min)
        form.addRow("Pace Final", self.edt_pace_max)
        form.addRow("Observação", self.edt_notes)

        layout.addLayout(form)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Tipo",
            "Distância",
            "Repetições",
            "Pace",
            "Observação",
        ])

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        layout.addWidget(self.table)

        buttons = QHBoxLayout()

        self.btn_add = QPushButton("Adicionar")
        self.btn_remove = QPushButton("Remover")
        self.btn_save = QPushButton("Salvar")
        self.btn_cancel = QPushButton("Cancelar")

        buttons.addWidget(self.btn_add)
        buttons.addWidget(self.btn_remove)
        buttons.addStretch()
        buttons.addWidget(self.btn_save)
        buttons.addWidget(self.btn_cancel)

        layout.addLayout(buttons)

        self.btn_add.clicked.connect(self.add_step)
        self.btn_remove.clicked.connect(self.remove_step)
        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        self.refresh_table()

    def refresh_table(self):

        self.table.clearContents()
        self.table.setRowCount(len(self.steps))

        for row, step in enumerate(self.steps):

            self.table.setItem(
                row,
                0,
                QTableWidgetItem(step["type"])
            )

            self.table.setItem(
                row,
                1,
                QTableWidgetItem(f'{step["distance"]:.3f}')
            )

            self.table.setItem(
                row,
                2,
                QTableWidgetItem(str(step["repetitions"]))
            )

            self.table.setItem(
                row,
                3,
                QTableWidgetItem(
                    f'{step["pace_min"]} - {step["pace_max"]}'
                )
            )

            self.table.setItem(
                row,
                4,
                QTableWidgetItem(step["notes"])
            )

    def add_step(self):

        self.steps.append({
            "type": self.cmb_type.currentText(),
            "distance": self.edt_distance.value(),
            "repetitions": self.edt_repetitions.value(),
            "pace_min": self.edt_pace_min.text(),
            "pace_max": self.edt_pace_max.text(),
            "notes": self.edt_notes.text(),
        })

        self.refresh_table()

        self.edt_distance.setValue(0)
        self.edt_repetitions.setValue(0)
        self.edt_pace_min.clear()
        self.edt_pace_max.clear()
        self.edt_notes.clear()

    def remove_step(self):

        row = self.table.currentRow()

        if row < 0:
            return

        del self.steps[row]

        self.refresh_table()

    def get_steps(self):

        return self.steps