import os
from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt


class HomeScreen(QWidget):

    def __init__(self, audio):
        super().__init__()
        self._audio = audio
        self.setWindowTitle("Inicio")
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)

        self.background_label = QLabel(self)
        img_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "resources", "images", "portada.png"
        )
        pixmap = QPixmap(img_path)
        if not pixmap.isNull():
            self.background_label.setPixmap(pixmap)
        self.background_label.setScaledContents(True)
        self.background_label.setGeometry(0, 0, 800, 600)

        button_layout = QVBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)
        button_layout.setSpacing(20)

        self.btn_play   = QPushButton("Jugar")
        self.btn_scores = QPushButton("Puntuaciones")
        self.btn_audio  = QPushButton()
        self.btn_exit   = QPushButton("Salir")

        _btn_style = """
            QPushButton {
                background-color: rgba(0, 0, 0, 150);
                color: white;
                font-size: 16px;
                padding: 10px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 200);
            }
        """

        for btn in (self.btn_play, self.btn_scores, self.btn_audio, self.btn_exit):
            btn.setFixedWidth(200)
            btn.setStyleSheet(_btn_style)
            button_layout.addWidget(btn)

        self.btn_audio.clicked.connect(self._toggle_audio)
        self._update_audio_button()

        main_layout.addStretch()
        main_layout.addLayout(button_layout)
        main_layout.addStretch()

    def showEvent(self, event):
        if self._audio.is_enabled():
            self._audio.play_music("menu")

    def _toggle_audio(self):
        estado = self._audio.toggle_audio()

        if estado:
            self._audio.play_effect("click")
            self._audio.play_music("menu")
        else:
            self._audio.stop_music()

        self._update_audio_button()

    def _update_audio_button(self):
        if self._audio.is_enabled():
            self.btn_audio.setText("🔊 Audio ON")
        else:
            self.btn_audio.setText("🔇 Audio OFF")

    def resizeEvent(self, event):
        self.background_label.setGeometry(0, 0, self.width(), self.height())