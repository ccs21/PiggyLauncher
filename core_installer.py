"""RetroArch 코어 설치 여부 확인과 선택적 다운로드.
경로 계산은 CoreInstaller, 네트워크·파일 작업은 CoreDownloadWorker, 진행 화면은 호출부가 담당한다.
"""

import os
import json
import shutil
import zipfile
import tempfile
import requests
from dataclasses import dataclass
from PySide6.QtCore import QThread, Signal


class CoreDownloadWorker(QThread):
    progress_changed = Signal(int)
    status_changed = Signal(str)
    indeterminate_changed = Signal(bool)
    finished_ok = Signal(str)
    finished_error = Signal(str)

    def __init__(self, core_name: str, retroarch_dir: str, parent=None):
        super().__init__(parent)
        self.core_name = core_name
        self.retroarch_dir = retroarch_dir

    def run(self):
        """ZIP 다운로드를 먼저 시도하고 실패하면 DLL 경로를 시도한다. 결과·진행률은 Qt 시그널로 GUI에 전달한다."""
        try:
            os.makedirs(os.path.join(self.retroarch_dir, "cores"), exist_ok=True)
            self.status_changed.emit("코어 다운로드 준비 중…")
            self.indeterminate_changed.emit(True)
            base = "https://buildbot.libretro.com/nightly/windows/x86_64/latest"
            name = CoreInstaller.normalized_core_name(self.core_name)
            dll_name = f"{name}_libretro.dll"
            zip_name = f"{name}_libretro.dll.zip"
            zip_url = f"{base}/{zip_name}"
            dll_url = f"{base}/{dll_name}"
            ok = self._download_and_install(zip_url, expect_zip=True)
            if not ok:
                ok = self._download_and_install(dll_url, expect_zip=False)
            if not ok:
                self.finished_error.emit(
                    "코어 다운로드에 실패했습니다. (네트워크/코어명 확인)"
                )
                return
            self.indeterminate_changed.emit(False)
            self.progress_changed.emit(100)
            self.status_changed.emit("설치 완료")
            self.finished_ok.emit("코어 설치를 완료했습니다.")
        except Exception as e:
            self.finished_error.emit(f"설치 중 오류 발생: {e}")

    def _download_and_install(self, url: str, expect_zip: bool) -> bool:
        """네트워크 응답을 청크 단위로 임시 파일에 저장한 후 cores 폴더에 배치한다. 메모리에 압축 파일 전체를 보관하지 않는다."""
        tmp_path = None
        staged_target = None
        try:
            msg = f"다운로드 시도: {url}"
            self.status_changed.emit(msg)
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            with requests.get(url, stream=True, timeout=60, headers=headers) as r:
                if r.status_code != 200:
                    return False
                total = int(r.headers.get("Content-Length", "0"))
                received = 0
                chunk = 1024 * 256
                (tmp_fd, tmp_path) = tempfile.mkstemp(
                    suffix=".zip" if expect_zip else ".dll"
                )
                os.close(tmp_fd)
                with open(tmp_path, "wb") as f:
                    if total <= 0:
                        self.indeterminate_changed.emit(True)
                        for part in r.iter_content(chunk_size=chunk):
                            if part:
                                f.write(part)
                    else:
                        self.indeterminate_changed.emit(False)
                        for part in r.iter_content(chunk_size=chunk):
                            if part:
                                f.write(part)
                                received += len(part)
                                pct = int(received * 100 / total)
                                self.progress_changed.emit(max(0, min(100, pct)))
                cores_dir = os.path.join(self.retroarch_dir, "cores")
                os.makedirs(cores_dir, exist_ok=True)
                if expect_zip:
                    self.status_changed.emit("압축 해제 중…")
                    with zipfile.ZipFile(tmp_path, "r") as zf:
                        dll_members = [
                            m
                            for m in zf.namelist()
                            if m.lower().endswith("_libretro.dll")
                        ]
                        if not dll_members:
                            try:
                                os.remove(tmp_path)
                            except Exception:
                                pass
                            return False
                        expected = f"{CoreInstaller.normalized_core_name(self.core_name)}_libretro.dll"
                        member = next(
                            (
                                m
                                for m in dll_members
                                if os.path.basename(m).lower() == expected.lower()
                            ),
                            None,
                        )
                        if member is None:
                            return False
                        target = os.path.join(cores_dir, os.path.basename(member))
                        # 완전히 추출한 파일만 교체한다. 압축 오류가 기존 DLL을 망가뜨리지 않게 한다.
                        fd, staged_target = tempfile.mkstemp(
                            dir=cores_dir, suffix=".partial"
                        )
                        os.close(fd)
                        with zf.open(member) as src, open(staged_target, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                        os.replace(staged_target, target)
                        staged_target = None
                else:
                    dll_name = os.path.basename(url)
                    target = os.path.join(cores_dir, dll_name)
                    fd, staged_target = tempfile.mkstemp(
                        dir=cores_dir, suffix=".partial"
                    )
                    os.close(fd)
                    shutil.copyfile(tmp_path, staged_target)
                    os.replace(staged_target, target)
                    staged_target = None
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
                return True
        except Exception:
            return False
        finally:
            # 네트워크·ZIP 해제 실패도 임시 파일 정리를 통과한다.
            for path in (tmp_path, staged_target):
                if path and os.path.exists(path):
                    os.remove(path)


@dataclass
class RetroArchInfo:
    retroarch_dir: str
    cores_dir: str


class CoreInstaller:
    CORE_NAME_MAP = {}

    @staticmethod
    def ensure_retroarch_path() -> RetroArchInfo | None:
        """
        configs/emul_config.json에서 RetroArch 경로 확인
        """
        try:
            with open(
                os.path.join("configs", "emul_config.json"), "r", encoding="utf-8"
            ) as f:
                conf = json.load(f)
                exe = (conf.get("executables", {}) or {}).get("RetroArch", "").strip()
                if not exe:
                    return None
                retro_dir = os.path.dirname(os.path.abspath(exe))
                cores_dir = os.path.join(retro_dir, "cores")
                return RetroArchInfo(retroarch_dir=retro_dir, cores_dir=cores_dir)
        except Exception:
            return None

    @staticmethod
    def normalized_core_name(core_name: str) -> str:
        """표시용 코어 이름을 DLL 이름으로 정규화한다. 매핑에 없으면 입력을 그대로 사용한다."""
        return CoreInstaller.CORE_NAME_MAP.get(core_name, core_name)

    @staticmethod
    def core_dll_path(retroarch_dir: str, core_name: str) -> str:
        """설치 루트와 정규화된 코어 이름으로 예상 DLL 위치를 계산한다. 파일을 생성하지 않는다."""
        name = CoreInstaller.normalized_core_name(core_name)
        return os.path.join(retroarch_dir, "cores", f"{name}_libretro.dll")

    @staticmethod
    def is_installed(retroarch_dir: str, core_name: str) -> bool:
        """예상 DLL의 존재 여부를 확인한다. 존재 확인은 DLL의 호환성·정상 동작 검증과 다르다."""
        return os.path.exists(CoreInstaller.core_dll_path(retroarch_dir, core_name))
