"""확인 대화상자와 진행률·코어 다운로드 표시를 위한 공통 UI.
네트워크 작업은 worker가 수행하고 UI는 진행/완료 시그널을 받는다.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QProgressBar,
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont, QKeyEvent


class ConfirmDialog(QDialog):
    def __init__(self, title, message, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        scale_px = self.theme_manager.scale_px
        self.setWindowTitle(title)
        self.setFixedSize(scale_px(520), scale_px(320))
        self.setWindowFlags(
            Qt.Dialog
            | Qt.CustomizeWindowHint
            | Qt.WindowTitleHint
            | Qt.WindowStaysOnTopHint
        )
        theme = self.theme_manager.get("popup", {})
        bg_color = theme.get("background_color", "#FFFFFF")
        confirm_bg = theme.get("confirm_button_background_color", "#007ACC")
        cancel_bg = theme.get("cancel_button_background_color", "#CCCCCC")
        cancel_text = theme.get("cancel_button_text_color", "#000000")
        border_px = scale_px(3)
        padding_px = scale_px(10)
        radius_px = scale_px(10)
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
        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        label.setFont(label_font)
        label.setStyleSheet(
            f"\n            font-family: '{label_family}';\n            font-size: {label_size}px;\n            font-weight: {('bold' if label_bold else 'normal')};\n            color: {label_color};\n            border: none;\n        "
        )
        layout.addWidget(label)
        btn_font_cfg = self.theme_manager.get("fonts.팝업버튼", label_font_cfg)
        btn_family = btn_font_cfg.get("family", "맑은 고딕")
        btn_size = btn_font_cfg.get("size", 20)
        btn_bold = btn_font_cfg.get("bold", True)
        btn_text_color = btn_font_cfg.get("color", "#FFFFFF")
        font_weight = "700" if btn_bold else "400"
        btn_font = QFont(btn_family, btn_size)
        btn_font.setBold(btn_bold)
        self.btn_ok = QPushButton("확인")
        self.btn_ok.setFont(btn_font)
        self.btn_ok.setFixedSize(scale_px(180), scale_px(60))
        self.btn_ok.setStyleSheet(
            f"\n            QPushButton {{\n                background-color: {confirm_bg};\n                color: {btn_text_color};\n                border: {border_px}px solid orange;\n                border-radius: {radius_px}px;\n                padding: {padding_px}px;\n                font-family: '{btn_family}';\n                font-size: {btn_size}px;\n                font-weight: {font_weight};\n            }}\n            QPushButton:pressed {{\n                background-color: {confirm_bg};\n            }}\n        "
        )
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("취소")
        self.btn_cancel.setFont(btn_font)
        self.btn_cancel.setFixedSize(scale_px(180), scale_px(60))
        self.btn_cancel.setStyleSheet(
            f"\n            QPushButton {{\n                background-color: {cancel_bg};\n                color: {cancel_text};\n                border: {border_px}px solid orange;\n                border-radius: {radius_px}px;\n                padding: {padding_px}px;\n                font-family: '{btn_family}';\n                font-size: {btn_size}px;\n                font-weight: {font_weight};\n            }}\n            QPushButton:pressed {{\n                background-color: {cancel_bg};\n            }}\n        "
        )
        self.btn_cancel.clicked.connect(self.reject)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(scale_px(40))
        button_layout.addStretch()
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        self.buttons = [self.btn_ok, self.btn_cancel]
        self.focus_index = 0
        self.update_button_styles()
        self.btn_ok.setFocus()

    def update_button_styles(self):
        for i, btn in enumerate(self.buttons):
            if i == self.focus_index:
                btn.setStyleSheet(
                    btn.styleSheet()
                    + f"QPushButton {{ border: {self.theme_manager.scale_px(3)}px solid orange; }}"
                )
            else:
                btn.setStyleSheet(btn.styleSheet() + "QPushButton { border: none; }")

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key in (Qt.Key_Return, Qt.Key_Enter):
            self.buttons[self.focus_index].click()
        elif key in (Qt.Key_Left, Qt.Key_A):
            self.focus_index = (self.focus_index - 1) % len(self.buttons)
            self.update_button_styles()
        elif key in (Qt.Key_Right, Qt.Key_D):
            self.focus_index = (self.focus_index + 1) % len(self.buttons)
            self.update_button_styles()
        elif key == Qt.Key_Escape:
            event.ignore()
        else:
            super().keyPressEvent(event)


class ProgressDialog(QDialog):
    """
    다운로드/설치 진행 상황 표시에 사용하는 프로그레스 팝업
    - 취소 버튼 없음(중도 종료로 인한 불안정 방지)
    - set_message(str), set_progress(int|None), set_indeterminate(bool) 제공
    - 작업 스레드가 있으면 connect_worker(worker)로 시그널 연결:
        * worker.progress_changed(int)          → 0~100 퍼센트
        * worker.status_changed(str)            → 상태 텍스트
        * worker.indeterminate_changed(bool)    → 불명 진행(바운싱) 토글
        * worker.finished_ok(str|None)          → 성공 메시지(옵션)
        * worker.finished_error(str)            → 실패 메시지
    """

    def __init__(self, title, message, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        scale_px = self.theme_manager.scale_px
        self._allow_close = False
        self.setWindowTitle(title)
        self.setFixedSize(scale_px(560), scale_px(280))
        self.setWindowFlags(
            Qt.Dialog
            | Qt.CustomizeWindowHint
            | Qt.WindowTitleHint
            | Qt.WindowStaysOnTopHint
        )
        theme = self.theme_manager.get("popup", {})
        bg_color = theme.get("background_color", "#FFFFFF")
        self.setStyleSheet(f"background-color: {bg_color};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            scale_px(30), scale_px(30), scale_px(30), scale_px(30)
        )
        layout.setSpacing(scale_px(20))
        label_font_cfg = self.theme_manager.get("fonts.팝업라벨", {})
        label_family = label_font_cfg.get("family", "맑은 고딕")
        label_size = label_font_cfg.get("size", 22)
        label_bold = label_font_cfg.get("bold", False)
        label_color = label_font_cfg.get("color", "#000000")
        self._label = QLabel(message)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setWordWrap(True)
        self._label.setStyleSheet(
            f"font-family: '{label_family}'; font-size: {label_size}px; font-weight: {('bold' if label_bold else 'normal')}; color: {label_color}; border: none;"
        )
        layout.addWidget(self._label)
        self._bar = QProgressBar()
        self._bar.setRange(0, 0)
        self._bar.setTextVisible(True)
        self._bar.setFormat("%p%")
        layout.addWidget(self._bar)
        btn_font_cfg = self.theme_manager.get("fonts.팝업버튼", label_font_cfg)
        btn_family = btn_font_cfg.get("family", "맑은 고딕")
        btn_size = btn_font_cfg.get("size", 20)
        btn_bold = btn_font_cfg.get("bold", True)
        btn_text_color = btn_font_cfg.get("color", "#FFFFFF")
        btn_font = QFont(btn_family, btn_size)
        btn_font.setBold(btn_bold)
        confirm_bg = theme.get("confirm_button_background_color", "#007ACC")
        border_px = scale_px(3)
        padding_px = scale_px(10)
        radius_px = scale_px(10)
        self._btn_close = QPushButton("닫기")
        self._btn_close.setFont(btn_font)
        self._btn_close.setFixedSize(scale_px(160), scale_px(54))
        self._btn_close.setStyleSheet(
            f"\n            QPushButton {{\n                background-color: {confirm_bg};\n                color: {btn_text_color};\n                border: {border_px}px solid orange;\n                border-radius: {radius_px}px;\n                padding: {padding_px}px;\n                font-family: '{btn_family}';\n                font-size: {btn_size}px;\n            }}\n        "
        )
        self._btn_close.clicked.connect(self.accept)
        self._btn_close.setVisible(False)
        layout.addWidget(self._btn_close, alignment=Qt.AlignCenter)

    def set_message(self, text: str):
        self._label.setText(text)

    def set_indeterminate(self, enabled: bool):
        if enabled:
            self._bar.setRange(0, 0)
        else:
            self._bar.setRange(0, 100)

    def set_progress(self, value: int | None):
        """
        value가 None이면 indeterminate 유지
        0 <= value <= 100 이면 determinate로 전환하여 설정
        """
        if value is None:
            self.set_indeterminate(True)
        else:
            if self._bar.maximum() != 100:
                self.set_indeterminate(False)
            self._bar.setValue(max(0, min(100, int(value))))

    def enable_close(self, enabled: bool, show_button: bool = True):
        """
        작업 완료 후 닫기 허용/버튼 표시
        """
        self._allow_close = enabled
        self._btn_close.setVisible(bool(show_button))

    def closeEvent(self, event):
        if not self._allow_close:
            event.ignore()
        else:
            super().closeEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if not self._allow_close and event.key() == Qt.Key_Escape:
            event.ignore()
            return
        super().keyPressEvent(event)

    def connect_worker(self, worker):
        """
        worker는 다음 시그널을 가질 수 있습니다(존재하는 것만 연결):
          - progress_changed(int)
          - status_changed(str)
          - indeterminate_changed(bool)
          - finished_ok(str|None)
          - finished_error(str)
        """
        if hasattr(worker, "progress_changed"):
            worker.progress_changed.connect(self._on_worker_progress)
        if hasattr(worker, "status_changed"):
            worker.status_changed.connect(self._on_worker_status)
        if hasattr(worker, "indeterminate_changed"):
            worker.indeterminate_changed.connect(self._on_worker_indeterminate)
        if hasattr(worker, "finished_ok"):
            worker.finished_ok.connect(self._on_worker_done_ok)
        if hasattr(worker, "finished_error"):
            worker.finished_error.connect(self._on_worker_done_error)

    @Slot(int)
    def _on_worker_progress(self, v: int):
        self.set_progress(v)

    @Slot(str)
    def _on_worker_status(self, msg: str):
        self.set_message(msg)

    @Slot(bool)
    def _on_worker_indeterminate(self, b: bool):
        self.set_indeterminate(b)

    @Slot(str)
    def _on_worker_done_ok(self, msg: str | None):
        if msg:
            self.set_message(msg)
        self.set_progress(100)
        self.enable_close(True, show_button=True)

    @Slot(str)
    def _on_worker_done_error(self, msg: str):
        self.set_message(msg or "실패했습니다.")
        self.enable_close(True, show_button=True)
