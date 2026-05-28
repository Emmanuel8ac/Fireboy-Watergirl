from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QSizePolicy


class IntroScreen(QWidget):
    open_connection = Signal()

    def __init__(self, audio):
        super().__init__()
        self._audio = audio
        self.frames = []
        self.current_frame = 0

        self.setAutoFillBackground(True)
        self.setStyleSheet("background-color: black;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._build_ui()
        self._load_frames()
        self._start_animation()

    # Crea la interfaz principal
    def _build_ui(self):
        base_dir = Path(__file__).resolve().parent.parent.parent

        # Título principal
        self.lbl_title = QLabel(self)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setScaledContents(True)

        title_path = base_dir / "resources" / "ui" / "menu" / "title.png"
        self.lbl_title.setPixmap(QPixmap(str(title_path)))

        # Animación central
        self.anim_label = QLabel(self)
        self.anim_label.setAlignment(Qt.AlignCenter)
        self.anim_label.setStyleSheet("background: transparent;")

        # Botón de inicio
        self.btn_play = QPushButton(self)
        self.btn_play.setStyleSheet("border: none; background: transparent;")
        self.btn_play.setCursor(Qt.PointingHandCursor)
        self.btn_play.clicked.connect(self.open_connection.emit)

        play_path = base_dir / "resources" / "ui" / "buttons" / "btn_play" / "1_up.png"
        pixmap = QPixmap(str(play_path))

        if not pixmap.isNull():
            self.btn_play.setIcon(QIcon(pixmap))
            self.btn_play.setIconSize(pixmap.size())
            self.btn_play.setFixedSize(pixmap.size())
        else:
            self.btn_play.setText("JUGAR")
            self.btn_play.setFixedSize(180, 70)

    # Carga los frames de la animación
    def _load_frames(self):
        base_dir = Path(__file__).resolve().parent.parent.parent
        folder = base_dir / "resources" / "ui" / "menu" / "animation_particles"

        if not folder.exists():
            return

        files = sorted(folder.glob("*.png"), key=lambda path: int(path.stem) if path.stem.isdigit() else 999)

        for file in files:
            pixmap = QPixmap(str(file))
            if not pixmap.isNull():
                self.frames.append(pixmap)

    # Inicia la animación
    def _start_animation(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_frame)
        self.timer.start(50)

    # Actualiza el frame actual
    def _update_frame(self):
        if not self.frames:
            return

        target_w = max(180, int(self.width() * 0.32))
        target_h = max(120, int(self.height() * 0.24))

        frame = self.frames[self.current_frame].scaled(
            target_w,
            target_h,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.anim_label.setPixmap(frame)
        self.current_frame = (self.current_frame + 1) % len(self.frames)

    # Ajusta posiciones al cambiar tamaño
    def resizeEvent(self, event):
        w = self.width()
        h = self.height()

        title_h = int(h * 0.24)
        self.lbl_title.setGeometry(0, int(h * 0.04), w, title_h)

        anim_w = int(w * 0.38)
        anim_h = int(h * 0.28)
        anim_x = (w - anim_w) // 2
        anim_y = int(h * 0.52)

        self.anim_label.setGeometry(anim_x, anim_y, anim_w, anim_h)

        self.btn_play.move(
            (w - self.btn_play.width()) // 2,
            anim_y + anim_h - self.btn_play.height() // 2
        )

        super().resizeEvent(event)

    # Reproduce música al mostrar la pantalla
    def showEvent(self, event):
        if self._audio:
            self._audio.play_music("intro")

        super().showEvent(event)

    # Detiene el temporizador al cerrar
    def closeEvent(self, event):
        if hasattr(self, "timer"):
            self.timer.stop()

        super().closeEvent(event)

