import os
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap

_IMG = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "images")


class PlayerSetupScreen(QWidget):

    def __init__(self):
        super().__init__()
        self.j1 = None
        self.j2 = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(20)

        self.lbl_title = QLabel("SELECCIONA TU PERSONAJE")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setFont(QFont("Arial", 20, QFont.Bold))

        chars_layout = QHBoxLayout()
        chars_layout.setSpacing(40)
        chars_layout.setAlignment(Qt.AlignCenter)

        self.fire_card,  self.fire_button  = self._make_card(
            "Fireboy",
            os.path.join(_IMG, "fire.png"),
            ["Resistente al Fuego", "Derrite Hielo"]
        )
        self.water_card, self.water_button = self._make_card(
            "Watergirl",
            os.path.join(_IMG, "water.png"),
            ["Resistente al Agua", "Congela Agua"]
        )

        chars_layout.addWidget(self.fire_card)
        chars_layout.addWidget(self.water_card)

        self.lbl_selected = QLabel("J1: -    J2: -")
        self.lbl_selected.setAlignment(Qt.AlignCenter)

        self.btn_ready = QPushButton("LISTO")
        self.btn_ready.setEnabled(False)
        self.btn_ready.setFixedWidth(200)

        layout.addWidget(self.lbl_title)
        layout.addLayout(chars_layout)
        layout.addWidget(self.lbl_selected)
        layout.addWidget(self.btn_ready, alignment=Qt.AlignCenter)

        self.fire_button.clicked.connect(lambda: self._select("Fireboy"))
        self.water_button.clicked.connect(lambda: self._select("Watergirl"))

    def _make_card(self, name: str, image_path: str, abilities: list):
        card   = QFrame()
        layout = QVBoxLayout(card)
        card.setFixedWidth(250)

        lbl_name = QLabel(name)
        lbl_name.setAlignment(Qt.AlignCenter)
        lbl_name.setFont(QFont("Arial", 13, QFont.Bold))

        lbl_img = QLabel()
        px = QPixmap(image_path)
        if not px.isNull():
            lbl_img.setPixmap(
                px.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        lbl_img.setAlignment(Qt.AlignCenter)

        lbl_ab = QLabel("\n".join(f"• {a}" for a in abilities))
        lbl_ab.setAlignment(Qt.AlignLeft)

        btn = QPushButton("SELECCIONAR")

        layout.addWidget(lbl_name)
        layout.addWidget(lbl_img)
        layout.addWidget(lbl_ab)
        layout.addWidget(btn)

        card.setStyleSheet("""
            QFrame {
                border: 2px solid black;
                background-color: #f2e3c6;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton {
                background-color: #d9b38c;
                border: 2px solid black;
                padding: 6px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #c69c6d; }
        """)
        return card, btn

    def _select(self, character: str):
        if self.j1 is None:
            self.j1 = character
        elif self.j2 is None and character != self.j1:
            self.j2 = character
        self._refresh()

    def _refresh(self):
        self.lbl_selected.setText(
            f"J1: {self.j1 or '-'}    J2: {self.j2 or '-'}"
        )
        self.btn_ready.setEnabled(bool(self.j1 and self.j2))