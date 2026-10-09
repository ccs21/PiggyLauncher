# 독립 실습 실행

이 예제는 실제 운영 소스에서 가져온 서버가 아니다. 가상의 데이터와 새로 정의한 API를 사용한다. 런처에서 자동 실행하거나 운영 서비스로 전송하지 않는다.

## 로컬 로그인과 공지

프로젝트 루트에서 터미널을 두 개 연다. 두 터미널에 **본인이 만든 같은 실습 암호**를 환경변수 `LAB_PASSWORD`로 설정한다. 암호는 16자 이상이어야 한다. 입력한 명령이 셸 기록에 남을 수 있으므로 실제 서비스 암호는 사용하지 않는다.

첫 터미널:

```powershell
python examples/lab_server.py
```

둘째 터미널:

```powershell
python examples/lab_client.py
```

예상 결과는 로그인 확인 메시지와 가상 공지 두 개다. 클라이언트는 같은 공지를 두 번 큐에 넣으려 하지만 중복을 제거해 한 번씩 표시한다. 서버에서 Ctrl+C를 누르면 종료되며 메모리의 세션도 사라진다.

| 요청 | 응답 | 학습 목적 |
|---|---|---|
| POST /lab/login, JSON password | token, expires_in 또는 401 | 자격 확인과 세션 발급의 차이 |
| GET /lab/session, Bearer 토큰 | authenticated 또는 401 | 만료된 세션 판정 |
| GET /lab/notices | items: sequence, text | 수신 순서와 중복 처리 |

이 서버는 루프백 전용이며 공개 배포용이 아니다. 암호 검증은 가상 로그인 실습용이다. TLS·공개 웹 관리자·요청 제한과 실제 Qt 연결은 확장 과제다. POST /lab/logout에 Bearer 토큰을 보내면 해당 세션을 폐기한다.

## 영속 공지와 백업

notice_store.py는 SQLite 공지 작성·목록·백업 CLI다. LAB_NOTICE_DB를 해당 DB 경로로 설정하면 서버가 고정 예제 대신 저장된 공지를 제공한다. notice_sync.py는 페이지별 공지와 커서를 lab_data/inbox.local.json에 함께 저장하고 출력 후 큐에서 제거한다. 재시작·오프라인 실험 및 전체 명령은 [공지와 큐](../wiki/03-공지와-큐.md), [백업과 운영](../wiki/06-백업과-운영.md)에 있다. 단일 클라이언트 프로세스 기준이며 출력 직후 장애에는 재표시가 가능하다.

## 업데이트 API

```powershell
python examples/release_client.py --owner YOUR_ACCOUNT --repository YOUR_REPOSITORY
```

자신의 공개 저장소에 릴리즈를 만든 뒤 실행한다. 릴리즈 태그와 자산 이름·크기가 표시된다. 다운로드·설치·런처 교체는 하지 않는다. `verify_file`은 로컬 파일의 SHA-256 비교 함수이며 테스트에서 성공·불일치를 확인한다. 신뢰할 수 없는 곳에서 받은 해시를 비교하는 것만으로 배포자의 신원을 검증할 수는 없다.

## OAuth 함수 예제

`oauth_desktop.py`는 PKCE/state 생성과 인증 코드 교환 경계를 보여준다. 클라이언트 ID가 비어 있으면 요청을 시작하지 않는다. 시스템 브라우저 열기, 일회성 루프백 콜백, 시간 제한, 취소, ID 토큰 검증 및 앱 세션 생성은 별도 구현이 필요하다. 이 파일만으로 완성된 로그인 시스템이 되지는 않는다. [API 설정 안내](../wiki/API_SETUP.md)를 함께 읽는다.

## 자동 검증

### 선택적인 메일 전송

`smtp_optional.py`는 자동 장치 보고 기능을 대신하는 독립 실습이다. 아무 인수 없이 실행하면 아무것도 전송하지 않는다. 자신의 메일 공급자에서 SMTP 사용 권한과 앱 암호 발급 절차를 확인한 뒤 `LAB_SMTP_HOST`, `LAB_SMTP_USER`, `LAB_SMTP_PASSWORD`, `LAB_SMTP_TO`를 환경변수로 지정하고, 실제 전송을 원하는 경우에만 `--send`를 붙인다. 예제는 TLS 포트 465용이다. 공급자가 STARTTLS 또는 OAuth 인증만 지원한다면 해당 방식으로 코드를 바꿔야 한다. 기기 정보·매핑·개인 파일은 첨부하지 않는다.

### 테스트 실행

```powershell
python -m unittest discover -s tests -v
```

가상 암호·임시 폴더·임시 로컬 포트를 사용한다. 실제 Google·ScreenScraper 계정이나 게임은 사용하지 않는다.
