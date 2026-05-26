from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QLineEdit
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
        layout.setSpacing(24)

        self.lbl_title = QLabel("CONEXIÓN DE PARTIDA")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setFont(QFont("Arial", 22, QFont.Bold))

        self.lbl_error = QLabel("")
        self.lbl_error.setAlignment(Qt.AlignCenter)
        self.lbl_error.setStyleSheet("color: #ffb0a0; font-size: 14px; font-weight: bold;")

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_error)
        layout.addWidget(self._create_section())
        layout.addWidget(self._join_section())

        self.btn_local = QPushButton("JUGAR LOCAL EN ESTA COMPUTADORA")
        self.btn_local.setFixedWidth(300)
        layout.addWidget(self.btn_local, alignment=Qt.AlignCenter)

        self.btn_back = QPushButton("REGRESAR")
        self.btn_back.setFixedWidth(170)
        layout.addWidget(self.btn_back, alignment=Qt.AlignCenter)
        layout.addStretch()
        self._apply_styles()

    def _create_section(self) -> QFrame:
        frame = QFrame()
        box = QVBoxLayout(frame)
        lbl = QLabel("Crear partida")
        lbl.setFont(QFont("Arial", 15, QFont.Bold))
        row = QHBoxLayout()
        self.code_display = QLineEdit()
        self.code_display.setReadOnly(True)
        self.code_display.setPlaceholderText("Aquí aparecerá el código")
        self.btn_create = QPushButton("CREAR CÓDIGO")
        row.addWidget(self.code_display)
        row.addWidget(self.btn_create)
        box.addWidget(lbl)
        box.addLayout(row)
        return frame

    def _join_section(self) -> QFrame:
        frame = QFrame()
        box = QVBoxLayout(frame)
        lbl = QLabel("Unirse a partida")
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

    def reset(self):
        self.lbl_error.setText("")
        self.code_display.clear()
        self.input_code.clear()
        self.btn_create.setEnabled(True)
        self.btn_create.setText("CREAR CÓDIGO")

    def set_code(self, code: str):
        self.code_display.setText(code)
        self.btn_create.setEnabled(False)
        self.btn_create.setText("ESPERANDO JUGADOR")
        self.lbl_error.setText("")

    def show_error(self, msg: str):
        self.lbl_error.setStyleSheet("color: #ffb0a0; font-size: 14px; font-weight: bold;")
        self.lbl_error.setText(msg)

    def show_info(self, msg: str):
        self.lbl_error.setStyleSheet("color: #d6ffd6; font-size: 14px; font-weight: bold;")
        self.lbl_error.setText(msg)

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #2b1b12; color: #f6dfb4; }
            QFrame { border: 2px solid #4a2c19; background-color: #f2e3c6; color: #21160e; border-radius: 12px; padding: 12px; }
            QLineEdit { padding: 8px; border: 2px solid #4a2c19; background-color: white; color: #111; border-radius: 6px; }
            QPushButton { background-color: #d9b38c; border: 2px solid #2f1b0e; color: #21160e; padding: 8px; border-radius: 7px; font-weight: bold; }
            QPushButton:hover { background-color: #efc58b; }
        """)
