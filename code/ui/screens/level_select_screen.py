from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


# Permite al anfitrión escoger el mapa
class LevelSelectScreen(QWidget):
    level_selected = Signal(int)

    # Inicializa los datos necesarios
    def __init__(self):
        super().__init__()
        self.level_buttons = []
        self._build_ui()

    # Construye los elementos visuales
    def _build_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #151515; color: #f7d35c; }
            QLabel#titulo { font-size: 34px; font-weight: bold; color: #ffd84a; }
            QLabel#texto { font-size: 15px; color: #f6dfb4; }
            QPushButton#nivel {
                background-color: #2b2b2b; border: 3px solid #d7aa25;
                color: #f7d35c; border-radius: 16px; font-size: 23px;
                font-weight: bold; min-width: 200px; min-height: 106px;
            }
            QPushButton#nivel:hover { background-color: #3d3420; border-color: #fff06a; }
            QPushButton#nivel:disabled { background-color: #252525; border-color: #655634; color: #817459; }
            QPushButton#regresar {
                background-color: #d8aa62; border: 2px solid #2f1b0e;
                color: #21160e; padding: 9px 18px; border-radius: 8px; font-weight: bold;
            }
        """)

        main = QVBoxLayout(self)
        main.setContentsMargins(80, 45, 80, 35)
        main.setSpacing(22)

        title = QLabel("ESCOGER NIVEL")
        title.setObjectName("titulo")
        title.setAlignment(Qt.AlignCenter)
        self.lbl_subtitle = QLabel("Los personajes ya están listos. Elige el mapa para comenzar.")
        self.lbl_subtitle.setObjectName("texto")
        self.lbl_subtitle.setAlignment(Qt.AlignCenter)
        main.addWidget(title)
        main.addWidget(self.lbl_subtitle)

        grid = QGridLayout()
        grid.setHorizontalSpacing(26)
        grid.setVerticalSpacing(26)
        descriptions = ("Introducción", "Ascenso con palancas", "Puente central", "Doble elevador")
        for number, description in enumerate(descriptions, start=1):
            button = QPushButton(f"NIVEL {number}\n{description}")
            button.setObjectName("nivel")
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda checked=False, n=number: self.level_selected.emit(n))
            self.level_buttons.append(button)
            grid.addWidget(button, (number - 1) // 2, (number - 1) % 2)
        main.addLayout(grid)

        bottom = QHBoxLayout()
        self.btn_back = QPushButton("REGRESAR A PERSONAJES")
        self.btn_back.setObjectName("regresar")
        self.btn_back.setCursor(Qt.PointingHandCursor)
        bottom.addStretch()
        bottom.addWidget(self.btn_back)
        bottom.addStretch()
        main.addLayout(bottom)

    # Habilita niveles para el creador o espera al invitado
    def configure_selection(self, can_choose: bool):
        for button in self.level_buttons:
            button.setEnabled(can_choose)
        self.btn_back.setEnabled(can_choose)
        if can_choose:
            self.lbl_subtitle.setText("Los personajes ya están listos. Elige el mapa para comenzar.")
            self.btn_back.setText("REGRESAR A PERSONAJES")
        else:
            self.lbl_subtitle.setText("Nivel terminado. Esperando que el creador escoja el siguiente mapa.")
            self.btn_back.setText("REGRESAR A PERSONAJES")
