# Importa y organiza las herramientas necesarias
from pathlib import Path
from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel, QSpacerItem, QSizePolicy
from PySide6.QtGui import QPixmap, QIcon, QFont
from PySide6.QtCore import Qt, QSize
from config import UI_DIR


# Muestra el menú principal
class HomeScreen(QWidget):
    # Inicializa los datos necesarios
    def __init__(self, audio):
        super().__init__()
        self._audio = audio
        self._build_ui()

    # Construye los elementos visuales
    def _build_ui(self):
        self.background_label = QLabel(self)
        bg_path = Path(UI_DIR) / "menu" / "background_menu.png"
        if bg_path.exists():
            self.background_label.setPixmap(QPixmap(str(bg_path)))
            self.background_label.setScaledContents(True)
        else:
            self.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #2b1b12, stop:1 #0f0b08);")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 35, 30, 25)
        layout.setAlignment(Qt.AlignCenter)

        title_path = Path(UI_DIR) / "menu" / "title.png"
        self.lbl_title = QLabel("Fireboy & Watergirl")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        if title_path.exists():
            px = QPixmap(str(title_path))
            self.lbl_title.setPixmap(px.scaled(560, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.lbl_title.setFont(QFont("Arial", 36, QFont.Bold))
            self.lbl_title.setStyleSheet("color: #f4d9a6;")

        self.btn_play = self._make_button("JUGAR", "btn_play", QSize(220, 80))
        self.btn_scores = self._make_button("PUNTAJES", "btn_highscores", QSize(210, 60))
        self.btn_exit = self._make_button("SALIR", "btn_backtomenu", QSize(180, 55))

        layout.addWidget(self.lbl_title)
        layout.addSpacerItem(QSpacerItem(1, 25, QSizePolicy.Minimum, QSizePolicy.Fixed))
        layout.addWidget(self.btn_play, alignment=Qt.AlignCenter)
        layout.addWidget(self.btn_scores, alignment=Qt.AlignCenter)
        layout.addWidget(self.btn_exit, alignment=Qt.AlignCenter)
        layout.addStretch()

        self.btn_audio = QPushButton(self)
        self.btn_audio.setFixedSize(48, 48)
        self.btn_audio.setCursor(Qt.PointingHandCursor)
        self.btn_audio.setStyleSheet("border: none; background: transparent;")
        self.btn_audio.clicked.connect(self._toggle_audio)
        self._update_audio_button()

    # Crea botones usando los recursos disponibles
    def _make_button(self, text: str, folder: str, fallback_size: QSize) -> QPushButton:
        button = QPushButton(text)
        button.setCursor(Qt.PointingHandCursor)
        icon_path = Path(UI_DIR) / "buttons" / folder / "1_up.png"
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            button.setIcon(QIcon(pixmap))
            button.setIconSize(pixmap.size())
            button.setFixedSize(pixmap.size())
            button.setText("")
            button.setStyleSheet("border: none; background: transparent;")
        else:
            button.setFixedSize(fallback_size)
            button.setFont(QFont("Arial", 15, QFont.Bold))
            button.setStyleSheet("""
                QPushButton { background-color: #d8aa62; border: 3px solid #3b2313; border-radius: 12px; }
                QPushButton:hover { background-color: #f0c984; }
            """)
        return button

    # Activa o desactiva audio
    def _toggle_audio(self):
        self._audio.play_effect("click")
        self._audio.toggle_audio()
        self._update_audio_button()

    # Actualiza el icono de sonido
    def _update_audio_button(self):
        path = Path(UI_DIR) / "buttons" / "btn_muter" / "1.png"
        if path.exists():
            pixmap = QPixmap(str(path))
            self.btn_audio.setIcon(QIcon(pixmap))
            self.btn_audio.setIconSize(QSize(40, 40))
            self.btn_audio.setText("" if self._audio.is_enabled() else "X")
            self.btn_audio.setStyleSheet("border: none; background: transparent; color: red; font-size: 22px; font-weight: bold;")
        else:
            self.btn_audio.setText("SONIDO" if self._audio.is_enabled() else "MUDO")

    # Ajusta elementos al cambiar tamaño
    def resizeEvent(self, event):
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        self.background_label.lower()
        self.btn_audio.move(self.width() - 60, self.height() - 60)
        super().resizeEvent(event)
