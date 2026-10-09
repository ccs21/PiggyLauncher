"""계정 없는 공개본의 첫 설정 화면. 독립 실습과 런처의 로컬 기능을 구분한다."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


def build_profile_tab(theme_manager):
    tab = QWidget()
    layout = QVBoxLayout(tab)
    text = QLabel(
        "Classic 학습용 공개본\n\n계정 없이 모든 로컬 기능을 사용할 수 있습니다.\n코드 읽기: docs/LEARNING_GUIDE.md\nAPI 설정: wiki/API_SETUP.md\n독립 서버 실습: examples/README.md"
    )
    text.setWordWrap(True)
    text.setStyleSheet("font-size: 22px; padding: 24px;")
    layout.addWidget(text)
    layout.addStretch()
    return tab
