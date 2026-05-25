from pathlib import Path
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
from config import CHARACTERS_DIR


class PlayerSetupScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.j1 = None
        self.j2 = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(18)

        self.lbl_title = QLabel("SELECCIONA LOS PERSONAJES")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setFont(QFont("Arial", 22, QFont.Bold))

        chars_layout = QHBoxLayout()
        chars_layout.setSpacing(40)
        chars_layout.setAlignment(Qt.AlignCenter)

        self.fire_card, self.fire_button = self._make_card(
            "Fireboy", Path(CHARACTERS_DIR) / "fireboy" / "FireBoy_running" / "1.png",
            ["Se mueve con A / D", "Salta con W", "Puede tocar lava"]
        )
        self.water_card, self.water_button = self._make_card(
            "Watergirl", Path(CHARACTERS_DIR) / "watergirl" / "WaterGirl_running" / "1.png",
            ["Se mueve con ← / →", "Salta con ↑", "Puede tocar agua"]
        )

        chars_layout.addWidget(self.fire_card)
        chars_layout.addWidget(self.water_card)

        self.lbl_selected = QLabel("J1: -    J2: -")
        self.lbl_selected.setAlignment(Qt.AlignCenter)
        self.lbl_selected.setFont(QFont("Arial", 13, QFont.Bold))

        buttons = QHBoxLayout()
        self.btn_back = QPushButton("REGRESAR")
        self.btn_ready = QPushButton("LISTO")
        self.btn_ready.setEnabled(False)
        self.btn_back.setFixedWidth(170)
        self.btn_ready.setFixedWidth(170)
        buttons.addStretch()
        buttons.addWidget(self.btn_back)
        buttons.addWidget(self.btn_ready)
        buttons.addStretch()

        layout.addWidget(self.lbl_title)
        layout.addLayout(chars_layout)
        layout.addWidget(self.lbl_selected)
        layout.addLayout(buttons)
        layout.addStretch()

        self.fire_button.clicked.connect(lambda: self._select("Fireboy"))
        self.water_button.clicked.connect(lambda: self._select("Watergirl"))
        self._apply_styles()

    def _make_card(self, name: str, image_path: Path, abilities: list):
        card = QFrame()
        card.setFixedWidth(280)
        box = QVBoxLayout(card)

        lbl_name = QLabel(name)
        lbl_name.setAlignment(Qt.AlignCenter)
        lbl_name.setFont(QFont("Arial", 16, QFont.Bold))

        lbl_img = QLabel()
        px = QPixmap(str(image_path))
        if not px.isNull():
            lbl_img.setPixmap(px.scaled(125, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            lbl_img.setText("🔥" if name == "Fireboy" else "💧")
            lbl_img.setFont(QFont("Arial", 70))
        lbl_img.setAlignment(Qt.AlignCenter)

        lbl_ab = QLabel("\n".join(f"• {a}" for a in abilities))
        lbl_ab.setAlignment(Qt.AlignLeft)
        btn = QPushButton("SELECCIONAR")

        box.addWidget(lbl_name)
        box.addWidget(lbl_img)
        box.addWidget(lbl_ab)
        box.addWidget(btn)
        return card, btn

    def _select(self, character: str):
        if self.j1 == character:
            self.j1 = None
        elif self.j2 == character:
            self.j2 = None
        elif self.j1 is None:
            self.j1 = character
        elif self.j2 is None:
            self.j2 = character
        self._refresh()

    def reset_selection(self):
        self.j1 = None
        self.j2 = None
        self._refresh()

    def _refresh(self):
        self.lbl_selected.setText(f"J1: {self.j1 or '-'}    J2: {self.j2 or '-'}")
        self.btn_ready.setEnabled(bool(self.j1 and self.j2))
        self.fire_button.setText("QUITAR" if "Fireboy" in (self.j1, self.j2) else "SELECCIONAR")
        self.water_button.setText("QUITAR" if "Watergirl" in (self.j1, self.j2) else "SELECCIONAR")

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #2b1b12; color: #f6dfb4; }
            QFrame { border: 2px solid #4a2c19; background-color: #f2e3c6; color: #21160e; border-radius: 12px; padding: 12px; }
            QPushButton { background-color: #d9b38c; border: 2px solid #2f1b0e; color: #21160e; padding: 8px; border-radius: 7px; font-weight: bold; }
            QPushButton:hover { background-color: #efc58b; }
            QPushButton:disabled { background-color: #8d8173; color: #4f4a44; }
        """)
