from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFrame, QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import random
import string


class ConnectionScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.main_layout.setAlignment(Qt.AlignTop)
        self.main_layout.setSpacing(25)

        self.lbl_title = QLabel("CONEXIÓN")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setFont(QFont("Arial", 20, QFont.Bold))

        self.create_section = self.create_create_section()
        self.join_section = self.create_join_section()

        self.btn_back = QPushButton("REGRESAR")
        self.btn_back.setFixedWidth(150)

        self.main_layout.addWidget(self.lbl_title)
        self.main_layout.addWidget(self.create_section)
        self.main_layout.addWidget(self.join_section)
        self.main_layout.addWidget(self.btn_back, alignment=Qt.AlignCenter)

        self.apply_styles()

    def create_create_section(self):
        frame = QFrame()
        layout = QVBoxLayout()
        frame.setLayout(layout)

        lbl = QLabel("Crear partida")
        lbl.setFont(QFont("Arial", 14, QFont.Bold))

        row = QHBoxLayout()

        self.code_display = QLineEdit()
        self.code_display.setReadOnly(True)
        self.code_display.setText(self.generate_code())

        self.btn_create = QPushButton("CREAR")
        self.btn_create.clicked.connect(self.generate_new_code)

        row.addWidget(self.code_display)
        row.addWidget(self.btn_create)

        layout.addWidget(lbl)
        layout.addLayout(row)

        return frame

    def create_join_section(self):
        frame = QFrame()
        layout = QVBoxLayout()
        frame.setLayout(layout)

        lbl = QLabel("Unirse a partida")
        lbl.setFont(QFont("Arial", 14, QFont.Bold))

        row = QHBoxLayout()

        self.input_code = QLineEdit()
        self.input_code.setPlaceholderText("Ingresa código")

        self.btn_join = QPushButton("UNIRSE")

        row.addWidget(self.input_code)
        row.addWidget(self.btn_join)

        layout.addWidget(lbl)
        layout.addLayout(row)

        return frame

    def generate_code(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    def generate_new_code(self):
        self.code_display.setText(self.generate_code())

    def apply_styles(self):
        self.setStyleSheet("""
            QFrame {
                border: 2px solid black;
                background-color: #f2e3c6;
                border-radius: 10px;
                padding: 10px;
            }

            QLabel {
                font-size: 14px;
            }

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

            QPushButton:hover {
                background-color: #c69c6d;
            }
        """)