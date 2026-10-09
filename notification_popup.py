"""한 건의 알림 화면과 페이드아웃을 담당한다.
닫힘 신호가 다음 큐 항목을 진행시킨다. 메시지 수신·중복 기록·게임 중 보류는 관리자의 책임이다.
"""

import logging
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtGui import QFont
import webbrowser


class NotificationPopup(QWidget):
    closed = Signal()

    def __init__(self, message, theme_manager, link=None, duration=10000, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.link = link
        scale_px = self.theme_manager.scale_px
        self.setWindowFlags(
            Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFixedWidth(scale_px(800))
        layout = QVBoxLayout()
        layout.setContentsMargins(
            scale_px(40), scale_px(40), scale_px(40), scale_px(40)
        )
        self.label = QLabel(message)
        self.label.setStyleSheet(f"color: white; padding-left: {scale_px(24)}px;")
        font = QFont("맑은 고딕", scale_px(24))
        font.setBold(True)
        self.label.setFont(font)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 204); border-radius: 8px;")
        if parent:
            parent_geo = parent.geometry()
            x = parent_geo.x() + scale_px(40)
            y = parent_geo.y() + parent_geo.height() - self.height() - scale_px(180)
            self.move(x, y)
        else:
            screen_geometry = self.screen().geometry()
            self.move(scale_px(40), screen_geometry.height() - scale_px(180))
        self.setWindowOpacity(1.0)
        self.show()
        QTimer.singleShot(duration, self.fade_out)

    def fade_out(self):
        """표시 시간이 끝나면 투명도를 줄인다. 실제 종료가 큐의 다음 항목을 깨운다."""
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(1000)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.finished.connect(self.close)
        self.animation.start()

    def mousePressEvent(self, event):
        if self.link:
            try:
                webbrowser.open(self.link)
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        self.close()

    def closeEvent(self, event):
        """시간 경과와 클릭 모두 동일한 완료 신호를 한 번만 보낸다."""
        if not getattr(self, "_closed_once", False):
            self._closed_once = True
            self.closed.emit()
            self.deleteLater()
        super().closeEvent(event)
