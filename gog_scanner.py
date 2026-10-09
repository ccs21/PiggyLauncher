"""GOG Galaxy의 로컬 설치 데이터베이스를 읽기 전용으로 조회한다.
구입 목록 전체가 아니라 설치된 게임의 실행 정보를 등록 후보로 만든다.
"""

import logging
import sqlite3
import os
from pathlib import Path


def get_db_path():
    """Galaxy의 로컬 DB 기본 경로를 확인한다. DB가 없으면 None이며 스캐너는 별도 DB를 만들어서는 안 된다."""
    default_path = "C:\\\\ProgramData\\\\GOG.com\\\\Galaxy\\\\storage\\\\galaxy-2.0.db"
    if os.path.exists(default_path):
        return default_path
    else:
        return None


def scan_gog_installed_games(db_path):
    """Galaxy 설치 테이블에서 제목·실행 파일·설치 폴더를 읽는다. 플랫폼 DB 구조에 의존하는 어댑터다."""
    results = []
    try:
        # connect(path)는 잘못된 경로에 빈 DB를 만들 수 있다. 설치 검색은 읽기 전용이다.
        conn = sqlite3.connect(Path(db_path).resolve().as_uri() + "?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute(
            "\n            SELECT\n                ibp.productId,\n                ld.title,\n                ibp.installationPath,\n                ptlp.executablePath\n            FROM InstalledBaseProducts AS ibp\n            LEFT JOIN LimitedDetails AS ld ON ibp.productId = ld.productId\n            LEFT JOIN PlayTasks AS pt ON pt.gameReleaseKey = 'gog_' || ibp.productId\n            LEFT JOIN PlayTaskLaunchParameters AS ptlp ON pt.id = ptlp.playTaskId\n        "
        )
        rows = cursor.fetchall()
        for row in rows:
            (product_id, title, install_path, exe_name) = row
            if not (title and install_path and exe_name):
                continue
            exe_full_path = os.path.join(install_path, exe_name)
            result = {
                "platform": "gog",
                "appid": f"gog_{product_id}",
                "title": title,
                "path": install_path,
                "exe": exe_name,
                "exe_full_path": exe_full_path,
            }
            results.append(result)
    except Exception as e:
        logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
    finally:
        if "conn" in locals():
            conn.close()
    return results


def main():
    """스캐너만 실행할 때의 진입점이다. 런처 UI를 띄우지 않고 로컬 설치 검색을 수행한다."""
    db_path = get_db_path()
    if not db_path:
        return
    scan_gog_installed_games(db_path)


if __name__ == "__main__":
    main()
