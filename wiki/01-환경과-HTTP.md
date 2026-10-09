# 1. 환경과 HTTP

## 실행

[프로젝트 README](../README.md)의 가상환경을 준비한 뒤 프로젝트 루트에서 터미널 두 개를 연다. 두 터미널 모두 아래와 같이 같은 **실습 전용 16자 이상 암호**를 설정한다. 실제 계정 암호는 사용하지 않는다.

```powershell
$python = (Resolve-Path .venv/Scripts/python.exe).Path
$secret = Read-Host '실습용 암호' -AsSecureString
$env:LAB_PASSWORD = [System.Net.NetworkCredential]::new('', $secret).Password
```

첫 터미널:

```powershell
& $python examples/lab_server.py
```

둘째 터미널:

```powershell
& $python examples/lab_client.py
```

예상 결과는 로그인 확인 메시지와 가상 공지 두 개다. 서버는 127.0.0.1:8000에만 바인딩한다. 종료는 첫 터미널에서 Ctrl+C, 각 터미널에서 `Remove-Item Env:LAB_PASSWORD`다. 실제 제품 서버에는 연결하지 않는다.

## 요청과 응답 읽기

[lab_server.py](../examples/lab_server.py)의 handler_for는 상태 객체를 공유하는 핸들러 클래스를 만든다. do_GET/do_POST는 요청을 분기하고 reply는 JSON을 UTF-8 바이트로 변환한다. Content-Length는 글자 수가 아닌 바이트 수다.

[lab_client.py](../examples/lab_client.py)는 timeout=5와 raise_for_status를 사용한다. 연결 실패, HTTP 오류, JSON 오류를 구분해서 읽는다.

| 실험 | 결과 | 의미 |
|---|---|---|
| 서버를 끄고 요청 | 연결 오류 | HTTP 응답 자체가 없음 |
| 틀린 암호 | 401 | 연결은 되었지만 인증 실패 |
| /missing 조회 | 404 | 경로 없음 |
| 빈 JSON 로그인 | 400 | 요청 형식 오류 |
| 정상 로그인 | 200 | 세션 발급 |

```powershell
curl.exe -i http://127.0.0.1:8000/missing
curl.exe -i -X POST -H 'Content-Type: application/json' --data '{}' http://127.0.0.1:8000/lab/login
```

내장 HTTP 서버는 프로토콜 학습용이다. 인터넷 운영 서버로 그대로 배포하지 않는다. [Python HTTP 서버 문서](https://docs.python.org/3.10/library/http.server.html)
