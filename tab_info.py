"""제품 운영 화면과 구분되는 학습용 아카이브의 출처 안내."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


def build_info_tab(theme_manager):
    tab = QWidget()
    layout = QVBoxLayout(tab)
    text = QLabel(
        "Piggy Launcher Classic — 학습용 소스\n원 개발: Retro-G-Boy\nGPT-6을 이용한 코드 정리 및 주석 보완\n\n이 소스 아카이브는 유지보수하지 않습니다.\n외부 구성요소의 라이선스는 THIRD_PARTY.md를 확인하세요."
    )
    text.setWordWrap(True)
    text.setStyleSheet("font-size: 22px; padding: 24px;")
    layout.addWidget(text)
    return tab
