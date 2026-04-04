from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap


class PlayerSetupScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.j1 = None
        self.j2 = None
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.main_layout.setAlignment(Qt.AlignTop)
        self.main_layout.setSpacing(20)

        self.lbl_title = QLabel("SELECCIONA TU PERSONAJE")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setFont(QFont("Arial", 20, QFont.Bold))

        self.characters_layout = QHBoxLayout()
        self.characters_layout.setSpacing(40)
        self.characters_layout.setAlignment(Qt.AlignCenter)

        self.fire_card, self.fire_button = self.create_character_card(
            "Fireboy",
            "resources/images/fire.png",
            ["Resistente al Fuego", "Derrite Hielo"]
        )

        self.water_card, self.water_button = self.create_character_card(
            "Watergirl",
            "resources/images/water.png",
            ["Resistente al Agua", "Congela Agua"]
        )

        self.characters_layout.addWidget(self.fire_card)
        self.characters_layout.addWidget(self.water_card)

        self.lbl_selected = QLabel("J1: -    J2: -")
        self.lbl_selected.setAlignment(Qt.AlignCenter)

        self.btn_ready = QPushButton("LISTO")
        self.btn_ready.setEnabled(False)
        self.btn_ready.setFixedWidth(200)

        self.main_layout.addWidget(self.lbl_title)
        self.main_layout.addLayout(self.characters_layout)
        self.main_layout.addWidget(self.lbl_selected)
        self.main_layout.addWidget(self.btn_ready, alignment=Qt.AlignCenter)

        self.connect_signals()

    def create_character_card(self, name, image_path, abilities):
        card = QFrame()
        layout = QVBoxLayout()
        card.setLayout(layout)

        card.setFixedWidth(250)

        lbl_name = QLabel(name)
        lbl_name.setAlignment(Qt.AlignCenter)

        lbl_image = QLabel()
        pixmap = QPixmap(image_path)
        lbl_image.setPixmap(pixmap.scaled(120, 120, Qt.KeepAspectRatio))
        lbl_image.setAlignment(Qt.AlignCenter)

        lbl_abilities = QLabel("\n".join(f"• {a}" for a in abilities))
        lbl_abilities.setAlignment(Qt.AlignLeft)

        btn_select = QPushButton("SELECCIONAR")

        layout.addWidget(lbl_name)
        layout.addWidget(lbl_image)
        layout.addWidget(lbl_abilities)
        layout.addWidget(btn_select)

        card.setStyleSheet("""
            QFrame {
                border: 2px solid black;
                background-color: #f2e3c6;
                border-radius: 10px;
                padding: 10px;
            }
        """)

        return card, btn_select

    def connect_signals(self):
        self.fire_button.clicked.connect(lambda: self.select_character("Fireboy"))
        self.water_button.clicked.connect(lambda: self.select_character("Watergirl"))

    def select_character(self, character):
        if self.j1 is None:
            self.j1 = character
        elif self.j2 is None and character != self.j1:
            self.j2 = character

        self.update_ui()

    def update_ui(self):
        self.lbl_selected.setText(f"J1: {self.j1 or '-'}    J2: {self.j2 or '-'}")

        if self.j1 and self.j2:
            self.btn_ready.setEnabled(True)