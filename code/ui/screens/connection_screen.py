from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from logic.network_manager import NetworkManager


class ConnectionScreen(QWidget):
    def __init__(self, network: NetworkManager):
        super().__init__()
        self._network = network
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(18)
        layout.setContentsMargins(90, 38, 90, 30)

        self.lbl_title = QLabel("PARTIDA EN RED")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setFont(QFont("Arial", 25, QFont.Bold))

        self.lbl_error = QLabel("")
        self.lbl_error.setWordWrap(True)
        self.lbl_error.setAlignment(Qt.AlignCenter)
        self.lbl_error.setMinimumHeight(40)

        layout.addWidget(self.lbl_title)
        layout.addWidget(self._name_section())
        layout.addWidget(self.lbl_error)
        layout.addWidget(self._create_section())
        layout.addWidget(self._join_section())

        self.btn_back = QPushButton("REGRESAR")
        self.btn_back.setFixedWidth(180)
        layout.addWidget(self.btn_back, alignment=Qt.AlignCenter)
        layout.addStretch()
        self._apply_styles()

    def _name_section(self) -> QFrame:
        frame = QFrame()
        box = QVBoxLayout(frame)
        lbl = QLabel("Nombre del jugador")
        lbl.setFont(QFont("Arial", 15, QFont.Bold))
        text = QLabel("Este nombre se mostrará al escoger personaje y en el historial de puntajes.")
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Escribe tu nombre")
        self.input_name.setMaxLength(18)
        box.addWidget(lbl)
        box.addWidget(text)
        box.addWidget(self.input_name)
        return frame

    def _create_section(self) -> QFrame:
        frame = QFrame()
        box = QVBoxLayout(frame)
        lbl = QLabel("Crear servidor")
        lbl.setFont(QFont("Arial", 15, QFont.Bold))
        text = QLabel("El creador de la sala seleccionará el nivel cuando ambos estén listos.")
        row = QHBoxLayout()
        self.code_display = QLineEdit()
        self.code_display.setReadOnly(True)
        self.code_display.setPlaceholderText("Aquí aparecerá el código")
        self.btn_create = QPushButton("CREAR CÓDIGO")
        row.addWidget(self.code_display)
        row.addWidget(self.btn_create)
        box.addWidget(lbl)
        box.addWidget(text)
        box.addLayout(row)
        return frame

    def _join_section(self) -> QFrame:
        frame = QFrame()
        box = QVBoxLayout(frame)
        lbl = QLabel("Unirse a un servidor")
        lbl.setFont(QFont("Arial", 15, QFont.Bold))
        row = QHBoxLayout()
        self.input_code = QLineEdit()
        self.input_code.setPlaceholderText("Código de 6 caracteres")
        self.input_code.setMaxLength(6)
        self.btn_join = QPushButton("UNIRSE")
        row.addWidget(self.input_code)
        row.addWidget(self.btn_join)
        box.addWidget(lbl)
        box.addLayout(row)
        return frame

    def player_name(self) -> str:
        return " ".join(self.input_name.text().strip().split())

    def reset(self):
        self.lbl_error.setText("")
        self.code_display.clear()
        self.input_code.clear()
        self.input_name.clear()
        self.btn_create.setEnabled(True)
        self.btn_create.setText("CREAR CÓDIGO")

    def set_code(self, code: str):
        self.code_display.setText(code)
        self.btn_create.setEnabled(False)
        self.btn_create.setText("ESPERANDO JUGADOR")
        self.lbl_error.setText("")

    def show_error(self, message: str):
        self.lbl_error.setStyleSheet("color: #ffb0a0; font-size: 14px; font-weight: bold;")
        self.lbl_error.setText(message)

    def show_info(self, message: str):
        self.lbl_error.setStyleSheet("color: #d6ffd6; font-size: 14px; font-weight: bold;")
        self.lbl_error.setText(message)

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #2b1b12; color: #f6dfb4; }
            QFrame { border: 2px solid #4a2c19; background-color: #f2e3c6; color: #21160e; border-radius: 12px; padding: 10px; }
            QLineEdit { padding: 8px; border: 2px solid #4a2c19; background-color: white; color: #111; border-radius: 6px; }
            QPushButton { background-color: #d9b38c; border: 2px solid #2f1b0e; color: #21160e; padding: 9px; border-radius: 7px; font-weight: bold; }
            QPushButton:hover { background-color: #efc58b; }
            QPushButton:disabled { background-color: #8d8173; color: #4f4a44; }
        """)
