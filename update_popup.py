"""학습본을 공식 바이너리로 덮어쓰지 않는 정적 안내 화면.

릴리즈 조회·검증은 examples/release_client.py에서 독립적으로 실습한다.
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton


class UpdatePopup(QDialog):
    def __init__(self, theme_manager, main_window=None, parent=None):
        super().__init__(parent or main_window)
        self.setWindowTitle("학습용 아카이브")
        layout = QVBoxLayout(self)
        label = QLabel(
            "이 공개본은 자동 업데이트하지 않습니다.\n업데이트 API 실습은 examples/release_client.py를 참고하세요."
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        close = QPushButton("닫기")
        close.clicked.connect(self.accept)
        layout.addWidget(close)
        self.resize(640, 220)
