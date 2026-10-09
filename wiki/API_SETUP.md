# API가 필요한 이유와 자신의 키 설정하기

공개본에는 서비스 자격 증명이 없다. 설정이 비어 있는 기능은 요청하지 않거나 설정 안내를 표시한다. 키가 없는 상태에서도 로컬 목록과 코드 학습은 가능하다.

## ScreenScraper: ROM 설명과 미디어

ROM의 이름·설명·이미지를 조회하기 위해 사용한다. `devid`와 `devpassword`는 개발자 자격 증명이고, `ssid`와 `sspassword`는 사용자 계정이다. 서로 대체하지 않는다. API 입력과 반환 형식은 [공식 API 문서](https://www.screenscraper.fr/webapi2.php)를 따른다.

1. ScreenScraper에 자신의 계정을 만든다.
2. 공식 사이트의 API 안내와 문의 창구를 통해 자신이 만드는 소프트웨어의 개발자 접근 권한과 발급 절차를 확인한다. 일반 회원 가입만으로 개발자 키가 발급된다고 가정하지 않는다.
3. 발급받은 값을 `SCREENSCRAPER_DEV_ID`, `SCREENSCRAPER_DEV_PASSWORD` 환경변수로 제공한다.
4. 또는 `config_examples/api_keys.example.json`을 `configs/api_keys.local.json`으로 복사하고 빈 값을 채운다. 이 파일은 평문이며 Git에서 제외된다.
5. 사용자 계정은 화면에서 입력하거나 `SCREENSCRAPER_USER`, `SCREENSCRAPER_PASSWORD` 환경변수로 제공한다. 공개본은 사용자 암호를 설정 파일에 저장하지 않는다.

키는 코드·로그·스크린샷·질문 게시물에 넣지 않는다. API는 요청 매개변수에 자격 증명을 사용하므로 전체 URL도 출력하면 안 된다. 사용량·동시 요청 한도와 발급 조건은 자신의 계정 및 공식 안내에서 확인한다.

## Google: 인증 과정 학습

런처 사용에는 계정이 필요하지 않다. Google 연동을 공부하려는 경우만 자신의 Google Cloud 프로젝트에서 OAuth 동의 화면과 테스트 사용자를 구성하고 **데스크톱 앱 유형** 클라이언트를 만든다. 발급받은 ID는 `GOOGLE_CLIENT_ID`, 발급 구성에서 필요한 비밀값은 `GOOGLE_CLIENT_SECRET` 환경변수로 제공하며 소스에 포함하지 않는다.

[Google 데스크톱 OAuth 안내](https://developers.google.com/identity/protocols/oauth2/native-app)를 기준으로 시스템 브라우저와 루프백 콜백을 사용한다. `examples/oauth_desktop.py`에서 PKCE와 state 확인을 읽고, 자신의 콜백을 연결한다. 토큰 교환 후에는 검증된 라이브러리로 ID 토큰의 서명·발급자·대상 클라이언트·만료를 검증해야 한다. JWT 내용을 디코딩하기만 하고 로그인 성공으로 처리하면 안 된다.

교재의 로컬 암호 로그인 서버는 OAuth 서버가 아니다. 두 실습을 섞어 실제 계정 인증이 구현됐다고 판단하지 않는다.

## GitHub: 릴리즈 조회

공개 릴리즈 조회 예제는 토큰 없이 동작한다. [GitHub Releases API 문서](https://docs.github.com/en/rest/releases/releases)를 참고해 자신의 저장소에 테스트 릴리즈를 만든다. 토큰이 필요한 별도 실습에서는 GitHub 계정 설정에서 해당 작업에 필요한 최소 권한의 토큰을 직접 발급하고 환경변수로만 제공한다. 공개본에 배포용 쓰기 권한 토큰을 내장하지 않는다.

`examples/release_client.py`의 소유자·저장소 인수는 필수다. 특정 제품의 업데이트 주소가 기본값으로 들어 있지 않다.

## Epic/STOVE 제목 매핑 실습

설치 정보의 제목과 상품 식별자를 연결하는 기능은 빈 연결 설정으로 남겼다. 자신의 학습용 JSON 서버를 만든 경우에만 `configs/services.local.json`의 `epic_slug_url`, `stove_slug_url`을 채운다. 외부 서버는 HTTPS, 로컬 예제는 루프백 HTTP를 허용한다.

예제 응답:

```json
[{"title":"Example Game","slug":"example-game","game_id":"123"}]
```

이는 공개 클라이언트의 입력 형식이며 실제 서비스의 수집기나 내부 저장 형식을 설명하는 자료가 아니다. 설정이 비어 있으면 해당 방식의 자동 매칭은 사용할 수 없다. 실제 상품 데이터는 자신이 사용할 권한이 있는 경로로 마련한다.

## 나머지 외부 연결

Steam·Epic·GOG·STOVE 웹 수집, Libretro 코어 다운로드, 게임 ID 표 조회 등 키 없는 외부 요청도 코드에 남아 있다. “운영 서비스 제거”는 오프라인 전용이라는 뜻이 아니다. 사이트 정책 변경·접속 제한·브라우저 인증 등에 따라 수집이 실패할 수 있다. 개인 브라우저 프로필은 제공하지 않으며 학습자가 만든 프로필 역시 커밋하지 않는다.
