"""자신의 공개 저장소 릴리즈를 조회한다. 설치·실행·자동 교체는 하지 않는다."""

import argparse
import hashlib
import hmac
import re
from pathlib import Path
import requests


def latest_release(owner, repository, session=None):
    if not all(re.fullmatch(r"[A-Za-z0-9_.-]+", s or "") for s in (owner, repository)):
        raise ValueError("자신의 GitHub 소유자와 저장소 이름을 입력하세요.")
    client = session or requests
    response = client.get(
        f"https://api.github.com/repos/{owner}/{repository}/releases/latest",
        headers={"Accept": "application/vnd.github+json"},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def verify_file(path, expected):
    """신뢰한 별도 경로에서 받은 SHA-256과 비교한다. 해시는 서명이 아니다."""
    if not re.fullmatch(r"[a-fA-F0-9]{64}", expected):
        raise ValueError("SHA-256 형식이 아닙니다.")
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return hmac.compare_digest(digest.hexdigest(), expected.lower())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repository", required=True)
    args = parser.parse_args()
    result = latest_release(args.owner, args.repository)
    print(result["tag_name"])
    for asset in result.get("assets", []):
        print(asset["name"], asset["size"])
