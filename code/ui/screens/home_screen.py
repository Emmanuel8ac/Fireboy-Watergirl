import os
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QTimer


class HomeScreen(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()
        self.load_animation()
        self.start_animation()

    # ================= UI =================
    def init_ui(self):
        self.setStyleSheet("background-color: black;")

        # ===== TÍTULO =====
        self.lbl_title = QLabel()
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setPixmap(QPixmap("resources/images/title.png"))

        # ===== ÁREA CENTRAL (ANIMACIÓN) =====
        self.animation_label = QLabel()
        self.animation_label.setFixedSize(400, 300)
        self.animation_label.setAlignment(Qt.AlignCenter)
        self.animation_label.setStyleSheet("""
            background-color: transparent;
        """)

        # ===== BOTÓN PLAY (IMAGEN) =====
        self.btn_play = QPushButton()
        self.btn_play.setCursor(Qt.PointingHandCursor)

        self.btn_play.setStyleSheet("""
            QPushButton {
                border: none;
            }
        """)

        self.btn_play.setIcon(QPixmap("resources/images/play.png"))
        self.btn_play.setIconSize(self.btn_play.icon().availableSizes()[0])

        # ===== LAYOUT =====
        layout = QVBoxLayout()

        layout.addStretch()
        layout.addWidget(self.lbl_title)
        layout.addSpacing(20)
        layout.addWidget(self.animation_label, alignment=Qt.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(self.btn_play, alignment=Qt.AlignCenter)
        layout.addStretch()

        self.setLayout(layout)

    # ================= ANIMACIÓN =================
    def load_animation(self):
        # Carpeta donde están los PNG (ej: frame_0.png, frame_1.png, ...)
        self.frames = []

        folder = "resources/particles"  # AJUSTA ESTA RUTA

        for file in sorted(os.listdir(folder)):
            if file.endswith(".png"):
                path = os.path.join(folder, file)
                self.frames.append(QPixmap(path))

        self.current_frame = 0

    def start_animation(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(50)  # velocidad (más bajo = más rápido)

    def update_frame(self):
        if not self.frames:
            return

        pixmap = self.frames[self.current_frame]

    def _update_audio_button(self):
        icon = "1.png" if self._audio.is_enabled() else "1.png"

        path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "resources", "ui", "buttons", "btn_muter", icon
        )

        self.animation_label.setPixmap(pixmap)

        self.current_frame = (self.current_frame + 1) % len(self.frames)
