import os
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QSizePolicy
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, QTimer


class IntroScreen(QWidget):

    def __init__(self, audio):
        super().__init__()
        self._audio = audio

        self.setAutoFillBackground(True)
        self.setStyleSheet("background-color: black;")

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._build_ui()
        self._load_frames()
        self._start_animation()

    # UI
    def _build_ui(self):

        # TÍTULO
        self.lbl_title = QLabel(self)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setScaledContents(True)

        title_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "resources", "ui", "menu", "title.png"
        )
        self.lbl_title.setPixmap(QPixmap(title_path))

        # ANIMACIÓN
        self.anim_label = QLabel(self)
        self.anim_label.setAlignment(Qt.AlignCenter)
        self.anim_label.setStyleSheet("background: transparent;")

        # BOTÓN PLAY
        self.btn_play = QPushButton(self)
        self.btn_play.setStyleSheet("border: none;")
        self.btn_play.setCursor(Qt.PointingHandCursor)

        play_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "resources", "ui", "buttons", "btn_play", "1_up.png"
        )

        pixmap = QPixmap(play_path)
        self.btn_play.setIcon(QIcon(pixmap))
        self.btn_play.setIconSize(pixmap.size())
        self.btn_play.setFixedSize(pixmap.size())

    # ANIMACIÓN
    def _load_frames(self):
        self.frames = []

        folder = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "resources", "ui", "menu", "animation_particles"
        )

        files = sorted(os.listdir(folder))

        for file in files:
            if file.endswith(".png"):
                path = os.path.join(folder, file)

                pixmap = QPixmap(path)

                # Escalar
                scaled = pixmap.scaled(
                    300, 200,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )

                self.frames.append(scaled)

        self.current_frame = 0

    def _start_animation(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)
        self.timer.start(50)

    def _update_frame(self):
        if not self.frames:
            return

        self.anim_label.setPixmap(self.frames[self.current_frame])
        self.current_frame = (self.current_frame + 1) % len(self.frames)

    # POSICIONES
    def resizeEvent(self, event):
        w = self.width()
        h = self.height()

        # TITULO
        title_h = int(h * 0.25)
        self.lbl_title.setGeometry(0, 20, w, title_h)

        # ANIMACION
        anim_w = int(w * 0.35)
        anim_h = int(h * 0.25)

        self.anim_label.setGeometry(
            (w - anim_w) // 2,
            int(h * 0.6),
            anim_w,
            anim_h
        )

        # BOTON PLAY
        self.btn_play.move(
            (w - self.btn_play.width()) // 2,
            int(h * 0.6) + anim_h - self.btn_play.height() // 2
        )

    # EVENTOS
    def showEvent(self, event):
        if self._audio:
            self._audio.play_music("intro")


