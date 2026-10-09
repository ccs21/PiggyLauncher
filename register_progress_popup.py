"""등록 작업의 진행 상태를 보여주는 작은 화면.
실제 등록은 수행하지 않으며 호출부가 제공한 텍스트·진행 정보를 표시한다.
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PySide6.QtGui import QMovie, QFont
from PySide6.QtCore import Qt, QSize


class RegisterProgressPopup(QDialog):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        scale_px = self.theme_manager.scale_px
        self.setWindowTitle("게임 등록 중")
        self.setFixedSize(scale_px(400), scale_px(300))
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        theme = self.theme_manager.get("popup", {})
        bg_color = theme.get("background_color", "#FFFFFF")
        scale_px(3)
        scale_px(10)
        scale_px(10)
        self.setStyleSheet(f"background-color: {bg_color};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            scale_px(40), scale_px(40), scale_px(40), scale_px(40)
        )
        layout.setSpacing(scale_px(30))
        label_font_cfg = self.theme_manager.get("fonts.팝업라벨", {})
        label_family = label_font_cfg.get("family", "맑은 고딕")
        label_size = label_font_cfg.get("size", 22)
        label_bold = label_font_cfg.get("bold", False)
        label_color = label_font_cfg.get("color", "#000000")
        label_font = QFont(label_family, label_size)
        label_font.setBold(label_bold)
        self.label = QLabel("게임 등록 중입니다...")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setFont(label_font)
        self.label.setStyleSheet(
            f"\n            font-family: '{label_family}';\n            font-size: {label_size}px;\n            font-weight: {('bold' if label_bold else 'normal')};\n            color: {label_color};\n            border: none;\n        "
        )
        layout.addWidget(self.label)
        gif_path = self.theme_manager.get("popup.loading_gif", "images/loading.gif")
        gif_size = scale_px(64)
        self.movie = QMovie(gif_path)
        self.movie.setScaledSize(QSize(gif_size, gif_size))
        self.gif_label = QLabel()
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.gif_label.setMovie(self.movie)
        layout.addWidget(self.gif_label)
        self.movie.start()

    def set_text(self, text):
        self.label.setText(text)

    def closeEvent(self, event):
        if hasattr(self, "movie"):
            self.movie.stop()
            self.movie.deleteLater()
        if hasattr(self, "gif_label"):
            self.gif_label.clear()
            self.gif_label.deleteLater()
        if hasattr(self, "label"):
            self.label.clear()
            self.label.deleteLater()
        super().closeEvent(event)
