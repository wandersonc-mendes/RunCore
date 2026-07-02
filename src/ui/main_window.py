from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.dashboard.page import DashboardPage
from ui.widgets.sidebar_button import SidebarButton


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("RunCore")
        self.resize(1400, 850)

        self.build_ui()

    def build_ui(self):

        root = QWidget()
        self.setCentralWidget(root)

        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ======================
        # MENU
        # ======================

        menu = QFrame()
        menu.setFixedWidth(220)

        menu.setStyleSheet("""
            background-color:#20232A;
        """)

        menu_layout = QVBoxLayout(menu)
        menu_layout.setContentsMargins(0, 0, 0, 20)

        titulo = QLabel("RUNCORE")
        titulo.setAlignment(Qt.AlignCenter)

        titulo.setStyleSheet("""
            color:white;
            font-size:22px;
            font-weight:bold;
            padding:20px;
        """)

        menu_layout.addWidget(titulo)
        menu_layout.addSpacing(20)

        self.btn_dashboard = SidebarButton("🏠 Dashboard")
        self.btn_atletas = SidebarButton("👤 Atletas")
        self.btn_planejamento = SidebarButton("📅 Planejamento")
        self.btn_arsenal = SidebarButton("📚 Arsenal")
        self.btn_evolucao = SidebarButton("📈 Evolução")
        self.btn_config = SidebarButton("⚙ Configurações")

        menu_layout.addWidget(self.btn_dashboard)
        menu_layout.addWidget(self.btn_atletas)
        menu_layout.addWidget(self.btn_planejamento)
        menu_layout.addWidget(self.btn_arsenal)
        menu_layout.addWidget(self.btn_evolucao)

        menu_layout.addStretch()

        menu_layout.addWidget(self.btn_config)

        # ======================
        # STACK
        # ======================

        self.stack = QStackedWidget()

        self.dashboard_page = DashboardPage()

        self.stack.addWidget(self.dashboard_page)

        layout.addWidget(menu)
        layout.addWidget(self.stack)

        # Página inicial
        self.stack.setCurrentWidget(self.dashboard_page)