from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFrame, QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from logic.network_manager import NetworkManager


class ConnectionScreen(QWidget):

    def __init__(self, network: NetworkManager):
        super().__init__()
        self._network = network
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(25)

        self.lbl_title = QLabel("CONEXIÓN")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setFont(QFont("Arial", 20, QFont.Bold))

        self.lbl_error = QLabel("")
        self.lbl_error.setAlignment(Qt.AlignCenter)
        self.lbl_error.setStyleSheet("color: red; font-size: 13px;")

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_error)
        layout.addWidget(self._create_section())
        layout.addWidget(self._join_section())

        self.btn_back = QPushButton("REGRESAR")
        self.btn_back.setFixedWidth(150)
        layout.addWidget(self.btn_back, alignment=Qt.AlignCenter)

        self._apply_styles()

    def _create_section(self) -> QFrame:
        frame  = QFrame()
        layout = QVBoxLayout(frame)

        lbl = QLabel("Crear partida")
        lbl.setFont(QFont("Arial", 14, QFont.Bold))

        row = QHBoxLayout()

        self.code_display = QLineEdit()
        self.code_display.setReadOnly(True)
        self.code_display.setPlaceholderText("— presiona CREAR —")

        self.btn_create = QPushButton("CREAR")
        self.btn_create.clicked.connect(self._on_create_clicked)

        row.addWidget(self.code_display)
        row.addWidget(self.btn_create)

        layout.addWidget(lbl)
        layout.addLayout(row)
        return frame

    def _join_section(self) -> QFrame:
        frame  = QFrame()
        layout = QVBoxLayout(frame)

        lbl = QLabel("Unirse a partida")
        lbl.setFont(QFont("Arial", 14, QFont.Bold))

        row = QHBoxLayout()

        self.input_code = QLineEdit()
        self.input_code.setPlaceholderText("Ingresa código (6 caracteres)")
        self.input_code.setMaxLength(6)

        self.btn_join = QPushButton("UNIRSE")

        row.addWidget(self.input_code)
        row.addWidget(self.btn_join)

        layout.addWidget(lbl)
        layout.addLayout(row)
        return frame

    def _on_create_clicked(self):
        code = self._network.create_room()
        self.code_display.setText(code)
        self.lbl_error.setText("")

    def show_error(self, msg: str):
        self.lbl_error.setText(msg)

    def _apply_styles(self):
        self.setStyleSheet("""
            QFrame {
                border: 2px solid black;
                background-color: #f2e3c6;
                border-radius: 10px;
                padding: 10px;
            }
            QLabel { font-size: 14px; }
            QLineEdit {
                padding: 6px;
                border: 1px solid black;
                background-color: white;
            }
            QPushButton {
                background-color: #d9b38c;
                border: 2px solid black;
                padding: 6px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #c69c6d; }
        """)