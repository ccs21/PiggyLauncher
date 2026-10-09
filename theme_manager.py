"""Classic의 theme_manager 모듈. 역할과 읽는 순서는 docs/SOURCE_MAP.md를 참고한다."""

import os
import json
from PySide6.QtGui import QFontDatabase


class ThemeManager:
    def __init__(self, theme_dir="theme/default", scale=1.0, resolution=(1920, 1080)):
        self.theme_dir = theme_dir
        self.scale = scale
        self.theme = {}
        self.loaded_fonts = {}
        (width, height) = resolution
        self.resolution_scale = min(width / 1920, height / 1080)
        self.load_theme()

    def load_theme(self):
        """theme.json을 로드하여 딕셔너리로 저장"""
        json_path = os.path.join(self.theme_dir, "theme.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                try:
                    self.theme = json.load(f)
                except Exception as e:
                    raise ValueError(f"[ERROR] theme.json 파싱 실패: {e}")
        else:
            raise FileNotFoundError(f"[WARN] 테마 파일 없음: {json_path}")

    def get(self, key, default=None):
        """'fonts.팝업라벨.size'처럼 점으로 구분한 키를 중첩 사전에서 찾는다.
        중간 키가 없으면 default를 반환한다. 호출부가 기본값을 명시해야 최소 테마에서도
        화면이 구성된다. 경로 문자열이라고 해서 실제 파일 존재를 확인하지는 않는다.
        """
        parts = key.split(".")
        value = self.theme
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        if isinstance(value, str):
            # 글꼴 이름·transparent·color 같은 일반 문자열을 경로로 바꾸면
            # 스타일시트가 깨진다. 파일 확장자가 있는 테마 자산만 상대 경로로 해석한다.
            if value and os.path.splitext(value)[1].lower() in (
                ".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".ico",
                ".wav", ".mp3", ".ttf", ".otf",
            ):
                return os.path.join(self.theme_dir, value)
            return value
        if key.startswith("fonts.") and isinstance(value, dict) and ("size" in value):
            value = value.copy()
            value["size"] = value["size"] * (self.resolution_scale / self.scale)
            if "file" in value and value["file"].strip():
                font_path = os.path.join(self.theme_dir, value["file"].strip())
                if os.path.exists(font_path):
                    if font_path not in self.loaded_fonts:
                        font_id = QFontDatabase.addApplicationFont(font_path)
                        if font_id != -1:
                            families = QFontDatabase.applicationFontFamilies(font_id)
                            if families:
                                self.loaded_fonts[font_path] = families[0]
                    if font_path in self.loaded_fonts:
                        value["family"] = self.loaded_fonts[font_path]
                else:
                    pass
            else:
                pass
            return value
        return value

    def scale_px(self, px: int) -> int:
        """DPI와 해상도 기반 스케일을 함께 고려하여 픽셀 수를 보정합니다."""
        final_scale = self.scale / self.resolution_scale
        return int(px / final_scale)
