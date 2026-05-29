# Importa y organiza las herramientas necesarias
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from config import CHARACTERS_DIR


# Permite que cada jugador elija un personaje
class PlayerSetupScreen(QWidget):
    selection_changed = Signal(str)
    continue_requested = Signal()

    # Inicializa los datos necesarios
    def __init__(self):
        super().__init__()
        self.is_host = False
        self.my_name = ""
        self.other_name = ""
        self.my_character = None
        self.other_character = None
        self._notice = ""
        self._build_ui()
        self.configure_online(False, "Jugador")

    # Construye los elementos visuales
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(16)
        layout.setContentsMargins(70, 35, 70, 26)

        self.lbl_title = QLabel("SELECCIÓN DE PERSONAJE")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setFont(QFont("Arial", 24, QFont.Bold))

        self.lbl_instruction = QLabel("")
        self.lbl_instruction.setAlignment(Qt.AlignCenter)
        self.lbl_instruction.setFont(QFont("Arial", 13))

        chars_layout = QHBoxLayout()
        chars_layout.setSpacing(38)
        chars_layout.setAlignment(Qt.AlignCenter)
        self.fire_card, self.fire_owner, self.fire_button = self._make_card(
            "Fireboy", Path(CHARACTERS_DIR) / "fireboy" / "FireBoy_running" / "1.png",
            ["Puede pasar por la lava", "Recoge diamantes rojos"],
        )
        self.water_card, self.water_owner, self.water_button = self._make_card(
            "Watergirl", Path(CHARACTERS_DIR) / "watergirl" / "WaterGirl_running" / "1.png",
            ["Puede pasar por el agua", "Recoge diamantes azules"],
        )
        chars_layout.addWidget(self.fire_card)
        chars_layout.addWidget(self.water_card)

        self.lbl_selected = QLabel("")
        self.lbl_selected.setAlignment(Qt.AlignCenter)
        self.lbl_selected.setFont(QFont("Arial", 14, QFont.Bold))

        # Muestra avisos sobre la selección
        self.lbl_notice = QLabel("")
        self.lbl_notice.setObjectName("notice")
        self.lbl_notice.setAlignment(Qt.AlignCenter)

        buttons = QHBoxLayout()
        self.btn_back = QPushButton("REGRESAR")
        self.btn_ready = QPushButton("ESPERANDO NIVEL")
        self.btn_back.setFixedWidth(180)
        self.btn_ready.setFixedWidth(250)
        buttons.addStretch()
        buttons.addWidget(self.btn_back)
        buttons.addWidget(self.btn_ready)
        buttons.addStretch()

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_instruction)
        layout.addLayout(chars_layout)
        layout.addWidget(self.lbl_selected)
        layout.addWidget(self.lbl_notice)
        layout.addLayout(buttons)
        layout.addStretch()

        self.fire_button.clicked.connect(lambda: self._select("Fireboy"))
        self.water_button.clicked.connect(lambda: self._select("Watergirl"))
        self.btn_ready.clicked.connect(self.continue_requested.emit)
        self._apply_styles()

    # Crea la tarjeta visual de un personaje
    def _make_card(self, name: str, image_path: Path, abilities: list):
        card = QFrame()
        card.setFixedWidth(300)
        box = QVBoxLayout(card)
        lbl_name = QLabel(name)
        lbl_name.setAlignment(Qt.AlignCenter)
        lbl_name.setFont(QFont("Arial", 17, QFont.Bold))
        lbl_img = QLabel()
        image = QPixmap(str(image_path))
        if not image.isNull():
            lbl_img.setPixmap(image.scaled(128, 158, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        lbl_img.setAlignment(Qt.AlignCenter)
        lbl_abilities = QLabel("\n".join(f"- {ability}" for ability in abilities))
        owner = QLabel("")
        owner.setAlignment(Qt.AlignCenter)
        owner.setMinimumHeight(28)
        owner.setObjectName("owner")
        button = QPushButton("ESCOGER")
        box.addWidget(lbl_name)
        box.addWidget(lbl_img)
        box.addWidget(lbl_abilities)
        box.addWidget(owner)
        box.addWidget(button)
        return card, owner, button

    # Prepara la selección para dos jugadores
    def configure_online(self, is_host: bool, my_name: str, other_name: str = ""):
        self.is_host = is_host
        self.my_name = my_name or "Jugador"
        self.other_name = other_name
        self.my_character = None
        self.other_character = None

        role = "creador de la sala" if is_host else "jugador invitado"
        self.lbl_instruction.setText(
            f"{self.my_name}, eres {role}. Cada jugador elige solo un personaje."
        )

        self._notice = "Esperando que ambos jugadores elijan personaje."
        self._refresh()

    # Muestra el nombre remoto
    def set_remote_name(self, name: str):
        self.other_name = name.strip()
        self._refresh()

    # Reserva el personaje elegido
    def _select(self, character: str):
        if character == self.other_character:
            selected_by = self.other_name or "el otro jugador"
            self._notice = f"{character} ya fue elegido por: {selected_by}."
            self._refresh()
            return
        self.my_character = None if self.my_character == character else character
        self._notice = "Selección enviada. Esperando al otro jugador."
        self.selection_changed.emit(self.my_character or "")
        self._refresh()

    # Recibe la selección remota
    def set_remote_character(self, character: str, name: str = "") -> bool:
        if name:
            self.other_name = name
        character = character or None
        if character and character == self.my_character:
            if self.is_host:
                self.other_character = None
                self._notice = f"{self.other_name or 'El invitado'} intentó escoger tu personaje."
                self._refresh()
                return True
            self.my_character = None
            self.other_character = character
            self._notice = f"Elegido por: {self.other_name or 'creador de la sala'}. Selecciona el otro personaje."
            self.selection_changed.emit("")
            self._refresh()
            return False
        self.other_character = character
        self._notice = "Los dos personajes están listos." if self.my_character and self.other_character else "Esperando la elección del otro jugador."
        self._refresh()
        return False

    # Devuelve personajes por jugador
    def chosen_players(self):
        if self.is_host:
            return self.my_character, self.other_character
        return self.other_character, self.my_character

    # Indica quién eligió personaje
    def _owner_text(self, character: str) -> str:
        if character == self.my_character:
            return f"Elegido por: {self.my_name}"
        if character == self.other_character:
            return f"Elegido por: {self.other_name or 'otro jugador'}"
        return ""

    # Actualiza la selección visible
    def _refresh(self):
        remote = self.other_name or "Otro jugador"
        self.lbl_selected.setText(f"{self.my_name}: {self.my_character or '-'}    {remote}: {self.other_character or '-'}")
        ready = bool(self.my_character and self.other_character)
        self.btn_ready.setEnabled(ready and self.is_host)
        self.btn_ready.setText("ESCOGER NIVEL" if self.is_host else "ESPERANDO NIVEL")
        self.lbl_notice.setText(self._notice)
        self.fire_owner.setText(self._owner_text("Fireboy"))
        self.water_owner.setText(self._owner_text("Watergirl"))
        self.fire_button.setText("QUITAR" if self.my_character == "Fireboy" else "ESCOGER")
        self.water_button.setText("QUITAR" if self.my_character == "Watergirl" else "ESCOGER")
        self.fire_button.setEnabled(self.other_character != "Fireboy" or self.my_character == "Fireboy")
        self.water_button.setEnabled(self.other_character != "Watergirl" or self.my_character == "Watergirl")

    # Aplica colores y estilos
    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #2b1b12; color: #f6dfb4; }
            QFrame { border: 2px solid #4a2c19; background-color: #f2e3c6; color: #21160e; border-radius: 12px; padding: 12px; }
            QLabel#owner { color: #a53922; font-weight: bold; font-size: 13px; }
            QLabel#notice { color: #000000; font-weight: bold; font-size: 13px; }
            QPushButton { background-color: #d9b38c; border: 2px solid #2f1b0e; color: #21160e; padding: 9px; border-radius: 7px; font-weight: bold; }
            QPushButton:hover { background-color: #efc58b; }
            QPushButton:disabled { background-color: #8d8173; color: #4f4a44; }
        """)
