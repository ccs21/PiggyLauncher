"""팝업을 준비하는 동안 로딩 안내를 표시하는 진입점.
위젯 생성은 GUI 스레드 작업이라는 제약과 사용자 피드백 시점을 함께 읽는다.
"""

from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QMovie, QGuiApplication


def launch_popup_with_loading(popup_cls, *args, parent=None, **kwargs):
    if "parent" in kwargs:
        del kwargs["parent"]
    if parent:
        center_point = parent.window().frameGeometry().center()
        theme_manager = (
            parent.theme_manager if hasattr(parent, "theme_manager") else None
        )
    else:
        center_point = QGuiApplication.primaryScreen().geometry().center()
        theme_manager = None
    screen = QGuiApplication.screenAt(center_point) or QGuiApplication.primaryScreen()
    screen_geometry = screen.availableGeometry()
    scale_px = theme_manager.scale_px if theme_manager else lambda x: x
    loading = QDialog(parent)
    loading.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
    loading.setModal(True)
    loading.setAttribute(Qt.WA_TranslucentBackground)
    loading.setStyleSheet("background-color: rgba(0, 0, 0, 160);")
    loading.setGeometry(screen_geometry)
    layout = QVBoxLayout(loading)
    layout.setContentsMargins(scale_px(40), scale_px(40), scale_px(40), scale_px(40))
    layout.setSpacing(scale_px(20))
    layout.setAlignment(Qt.AlignCenter)
    loading_icon = QLabel()
    loading_icon.setAlignment(Qt.AlignCenter)
    movie = QMovie("theme/default/loading.gif")
    movie.setScaledSize(QSize(scale_px(128), scale_px(128)))
    loading_icon.setMovie(movie)
    movie.start()
    label = QLabel("불러오는 중입니다...")
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet(f"color: white; font-size: {scale_px(20)}px;")
    layout.addWidget(loading_icon)
    layout.addWidget(label)
    loading.show()

    def run_popup():
        popup = popup_cls(*args, parent=parent, **kwargs)
        movie.stop()
        loading_icon.clear()
        loading_icon.deleteLater()
        label.clear()
        label.deleteLater()
        loading.accept()
        popup.exec()

    QTimer.singleShot(100, run_popup)
