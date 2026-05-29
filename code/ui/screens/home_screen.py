from pathlib import Path

from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtGui import QPixmap, QIcon, QFont
from PySide6.QtCore import Qt, QSize, QRect

from config import UI_DIR


class HomeScreen(QWidget):
    def __init__(self, audio):
        super().__init__()
        self._audio = audio
        self._build_ui()

    def _build_ui(self):
        self.background_label = QLabel(self)
        self._load_background()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 25, 0, 25)
        layout.setSpacing(0)

        self.lbl_title = QLabel()
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self._load_title()

        self.btn_play = self._make_image_button(
            folder="btn_play",
            filename="1_up.png",
            fallback_text="JUGAR",
            fallback_size=QSize(230, 80),
        )

        self.btn_scores = self._make_image_button(
            folder="btn_highscores",
            filename="1_up.png",
            fallback_text="PUNTUACIONES",
            fallback_size=QSize(210, 60),
        )

        button_layout = QVBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(0)
        button_layout.setAlignment(Qt.AlignCenter)
        button_layout.addWidget(self.btn_play, alignment=Qt.AlignCenter)
        button_layout.addSpacing(60)
        button_layout.addWidget(self.btn_scores, alignment=Qt.AlignCenter)

        layout.addStretch(1)
        layout.addWidget(self.lbl_title, alignment=Qt.AlignCenter)
        layout.addSpacing(200)
        layout.addLayout(button_layout)
        layout.addStretch(2)

        self.btn_audio = QPushButton(self)
        self.btn_audio.setFixedSize(48, 48)
        self.btn_audio.setCursor(Qt.PointingHandCursor)
        self.btn_audio.setStyleSheet("border: none; background: transparent;")
        self.btn_audio.clicked.connect(self._toggle_audio)
        self._update_audio_button()

    def _load_background(self):
        bg_path = Path(UI_DIR) / "menu" / "background_menu.png"
        if bg_path.exists():
            self.background_label.setPixmap(QPixmap(str(bg_path)))
            self.background_label.setScaledContents(True)

    def _load_title(self):
        title_path = Path(UI_DIR) / "menu" / "title.png"
        if title_path.exists():
            pixmap = QPixmap(str(title_path))
            pixmap = pixmap.scaled(760, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lbl_title.setPixmap(pixmap)
            self.lbl_title.setFixedSize(pixmap.size())
        else:
            self.lbl_title.setText("Fireboy & Watergirl")
            self.lbl_title.setFont(QFont("Arial", 36, QFont.Bold))
            self.lbl_title.setStyleSheet("color: #f4d9a6;")
            self.lbl_title.setFixedHeight(90)

    def _make_image_button(self, folder, filename, fallback_text, fallback_size, scale=1.0):
        button = QPushButton()
        button.setCursor(Qt.PointingHandCursor)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        icon_path = Path(UI_DIR) / "buttons" / folder / filename

        if icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            pixmap = self._trim_transparent_area(pixmap)

            if scale != 1.0:
                pixmap = pixmap.scaled(
                    int(pixmap.width() * scale),
                    int(pixmap.height() * scale),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )

            button.setIcon(QIcon(pixmap))
            button.setIconSize(pixmap.size())
            button.setFixedSize(pixmap.size())
            button.setStyleSheet("border: none; background: transparent; padding: 0px; margin: 0px;")
        else:
            button.setText(fallback_text)
            button.setFixedSize(fallback_size)

        return button

    def _trim_transparent_area(self, pixmap):
        image = pixmap.toImage()

        if not image.hasAlphaChannel():
            return pixmap

        left = image.width()
        right = 0
        top = image.height()
        bottom = 0
        found_pixel = False

        for y in range(image.height()):
            for x in range(image.width()):
                if image.pixelColor(x, y).alpha() > 0:
                    found_pixel = True
                    left = min(left, x)
                    right = max(right, x)
                    top = min(top, y)
                    bottom = max(bottom, y)

        if not found_pixel:
            return pixmap

        rect = QRect(left, top, right - left + 1, bottom - top + 1)
        return QPixmap.fromImage(image.copy(rect))

    def _toggle_audio(self):
        enabled = self._audio.toggle_audio()

        if enabled:
            self._audio.play_music("menu")
        else:
            self._audio.stop_music()

        self._update_audio_button()

    def _update_audio_button(self):
        path = Path(UI_DIR) / "buttons" / "btn_muter" / "1.png"

        if path.exists():
            pixmap = QPixmap(str(path))
            self.btn_audio.setIcon(QIcon(pixmap))
            self.btn_audio.setIconSize(QSize(40, 40))
        else:
            self.btn_audio.setText("ON" if self._audio.is_enabled() else "OFF")

    def resizeEvent(self, event):
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        self.background_label.lower()
        self.btn_audio.move(self.width() - 60, self.height() - 60)
        super().resizeEvent(event)