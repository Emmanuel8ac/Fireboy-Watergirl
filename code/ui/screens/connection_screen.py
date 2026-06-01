from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget

from logic.network_manager import NetworkManager


# Pide el nombre y conecta la partida en red
class ConnectionScreen(QWidget):
    # Inicializa los datos necesarios
    def __init__(self, network: NetworkManager):
        super().__init__()
        self._network = network
        self._build_ui()

    # Conserva el diseño original y permite desplazamiento si falta espacio
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setObjectName("scroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        page = QWidget()
        page.setObjectName("page")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(44, 30, 44, 30)
        page_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        column = QWidget()
        column.setObjectName("column")
        column.setMaximumWidth(940)
        layout = QVBoxLayout(column)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(18)
        layout.setContentsMargins(46, 8, 46, 20)

        self.lbl_title = QLabel("PARTIDA EN RED")
        self.lbl_title.setObjectName("title")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setFont(QFont("Arial", 25, QFont.Bold))

        self.lbl_error = QLabel("")
        self.lbl_error.setObjectName("message")
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

        page_layout.addWidget(column)
        scroll.setWidget(page)
        outer.addWidget(scroll)
        self._apply_styles()

    # Crea una tarjeta del diseño original
    def _section(self):
        frame = QFrame()
        frame.setObjectName("section")
        box = QVBoxLayout(frame)
        box.setContentsMargins(16, 12, 16, 12)
        box.setSpacing(7)
        return frame, box

    # Solicita el nombre del jugador
    def _name_section(self) -> QFrame:
        frame, box = self._section()
        lbl = QLabel("Nombre del jugador")
        lbl.setObjectName("sectionTitle")
        lbl.setFont(QFont("Arial", 15, QFont.Bold))
        text = QLabel("Este nombre se mostrará al escoger personaje y en el historial de puntajes.")
        text.setObjectName("sectionText")
        text.setWordWrap(True)
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Escribe tu nombre")
        self.input_name.setMaxLength(18)
        box.addWidget(lbl)
        box.addWidget(text)
        box.addWidget(self.input_name)
        return frame


    # Permite crear una sala
    def _create_section(self) -> QFrame:
        frame, box = self._section()
        lbl = QLabel("Crear servidor")
        lbl.setObjectName("sectionTitle")
        lbl.setFont(QFont("Arial", 15, QFont.Bold))
        text = QLabel("El creador de la sala seleccionará el nivel cuando ambos estén listos.")
        text.setObjectName("sectionText")
        text.setWordWrap(True)
        row = QHBoxLayout()
        self.code_display = QLineEdit()
        self.code_display.setReadOnly(True)
        self.code_display.setPlaceholderText("Aquí aparecerá la IP")
        self.btn_create = QPushButton("CREAR SERVIDOR")
        row.addWidget(self.code_display, 1)
        row.addWidget(self.btn_create)
        box.addWidget(lbl)
        box.addWidget(text)
        box.addLayout(row)
        return frame

    # Permite unirse a una sala
    def _join_section(self) -> QFrame:
        frame, box = self._section()
        lbl = QLabel("Unirse a un servidor")
        lbl.setObjectName("sectionTitle")
        lbl.setFont(QFont("Arial", 15, QFont.Bold))
        text = QLabel("Escribe la IP que te compartió el creador.")
        text.setObjectName("sectionText")
        text.setWordWrap(True)
        row = QHBoxLayout()
        self.input_code = QLineEdit()
        self.input_code.setPlaceholderText("Ejemplo: 192.168.1.25")
        self.input_code.setMaxLength(15)
        self.btn_join = QPushButton("UNIRSE")
        row.addWidget(self.input_code, 1)
        row.addWidget(self.btn_join)
        box.addWidget(lbl)
        box.addWidget(text)
        box.addLayout(row)
        return frame

    # Devuelve el nombre escrito
    def player_name(self) -> str:
        return " ".join(self.input_name.text().strip().split())

    # Limpia la pantalla
    def reset(self):
        self.lbl_error.setText("")
        self.code_display.clear()
        self.input_code.clear()
        self.input_name.clear()
        self.btn_create.setEnabled(True)
        self.btn_create.setText("CREAR SERVIDOR")

    # Muestra la IP del servidor
    def set_code(self, code: str):
        self.code_display.setText(code)
        self.btn_create.setEnabled(False)
        self.btn_create.setText("ESPERANDO JUGADOR")
        self.lbl_error.setText("")

    # Muestra un error
    def show_error(self, message: str):
        self.lbl_error.setStyleSheet("color: #ffb0a0; font-size: 14px; font-weight: bold;")
        self.lbl_error.setText(message)

    # Muestra un aviso
    def show_info(self, message: str):
        self.lbl_error.setStyleSheet("color: #d6ffd6; font-size: 14px; font-weight: bold;")
        self.lbl_error.setText(message)

    # Aplica colores y estilos
    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget, #page, #column, QScrollArea#scroll, QScrollArea#scroll > QWidget > QWidget {
                background-color: #2b1b12; color: #f6dfb4;
            }
            QLabel#title { color: #f6dfb4; }
            QFrame#section {
                border: 2px solid #4a2c19; background-color: #f2e3c6;
                color: #21160e; border-radius: 12px; padding: 10px;
            }
            QFrame#section QLabel#sectionTitle, QFrame#section QLabel#sectionText {
                background-color: transparent; border: none; padding: 0; color: #21160e;
            }
            QLineEdit {
                padding: 8px; border: 2px solid #4a2c19; background-color: white;
                color: #111; border-radius: 6px;
            }
            QPushButton {
                background-color: #d9b38c; border: 2px solid #2f1b0e; color: #21160e;
                padding: 9px; border-radius: 7px; font-weight: bold;
            }
            QPushButton:hover { background-color: #efc58b; }
            QPushButton:disabled { background-color: #8d8173; color: #4f4a44; }
        """)
