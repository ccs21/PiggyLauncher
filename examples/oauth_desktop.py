"""Google 데스크톱 OAuth의 PKCE/state 준비와 토큰 교환 예제.

자동 로그인하지 않는다. 시스템 브라우저·루프백 콜백·ID 토큰 검증을 연결하는
전체 절차 및 남은 실습은 wiki/API_SETUP.md를 읽는다.
"""

import base64
import hashlib
import hmac
import os
import secrets
from urllib.parse import urlencode
import requests


def authorization_request(redirect_uri="http://127.0.0.1:8765/"):
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    if not client_id:
        raise ValueError("자신의 데스크톱 OAuth 클라이언트 ID를 설정하세요.")
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    query = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    return (
        "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(query),
        state,
        verifier,
    )


def exchange_code(
    code,
    received_state,
    expected_state,
    verifier,
    redirect_uri="http://127.0.0.1:8765/",
):
    if not expected_state or not hmac.compare_digest(received_state, expected_state):
        raise ValueError("OAuth state가 일치하지 않습니다.")
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    if not client_id or not code or not verifier:
        raise ValueError("OAuth 요청 정보가 부족합니다.")
    data = {
        "client_id": client_id,
        "code": code,
        "code_verifier": verifier,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    if secret:
        data["client_secret"] = secret
    response = requests.post(
        "https://oauth2.googleapis.com/token", data=data, timeout=15
    )
    response.raise_for_status()
    return response.json()
