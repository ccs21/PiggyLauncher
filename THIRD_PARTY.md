# 외부 구성요소와 리소스

이 공개본은 소스 배포본이다. 외부 EXE·DLL·게임 파일·수집 이미지·브라우저 프로필·기존 폰트는 포함하지 않는다. 자체 MIT 허가는 아래 구성요소의 이용 조건을 대신하지 않는다.

## Python 의존성

검증 환경에 설치한 직접·간접 의존성의 버전, 출처와 라이선스는 [의존성 목록](docs/DEPENDENCY_LICENSES.md)에 기록했다. 설치 버전은 requirements-lock.txt로 재현할 수 있다. 패키지 자체를 이 저장소에 복사하지 않는다.

- PySide6 / Qt: 화면·이벤트·스레드. LGPL/GPL 또는 상용 조건을 확인한다. 바이너리로 묶어 배포할 때에는 [Qt 고지](https://doc.qt.io/qtforpython-6/licenses.html)와 해당 모듈의 조건을 검토해야 한다.
- pygame / SDL: 입력 장치. pygame의 LGPL과 SDL 구성요소의 개별 조건이 적용된다.
- pywin32: Windows 연동. Python 계열 및 하위 구성요소별 고지가 포함되므로 설치 패키지의 전체 라이선스를 함께 확인한다.
- 알림음 재생은 Python 표준 winsound를 사용한다. 별도 simpleaudio 패키지는 필요하지 않다.

## 사용자가 별도로 준비하는 도구

| 도구 | 역할 | 확인한 상위 프로젝트 라이선스 |
|---|---|---|
| [VDFparse](https://github.com/Grub4K/VDFparse) | Steam appinfo 파싱 | MIT, Copyright 2021–2022 Grub4K |
| [ResolutionSwitcher](https://github.com/andrebocchini/ResolutionSwitcher) | 해상도 변경 | MIT, Copyright 2024 Andre Bocchini |
| [SDL_GameControllerDB](https://github.com/mdqinc/SDL_GameControllerDB) | 컨트롤러 매핑 자료 | Zlib, Copyright 1997–2025 Sam Lantinga |
| Libretro 코어 | 에뮬레이션 | 코어별로 다름. 다운로드하는 코어의 조건 확인 |

위 도구와 매핑 DB를 이 소스 묶음에 포함하지 않았다. 필요한 경우 각 프로젝트에서 받아 코드의 tools 경로에 배치한다. 재배포할 때에는 원본 라이선스·저작권 고지를 보존해야 한다. 특정 빌드의 추가 구성요소는 그 빌드의 고지가 기준이다. 실제 외부 실행 파일 호출은 이번 검증 대상이 아니다.

## 그림·글꼴·서비스

theme/default/placeholder.svg는 이 교육용 공개본을 위해 작성한 중립 도형이다. theme.json의 기존 이미지·폰트·개인 경로 참조는 정리했다. 게임사 아트워크와 플랫폼 로고를 소스와 함께 배포하지 않는다. 사용자가 외부 서비스에서 수집하는 미디어에는 원 권리자의 조건이 적용된다.

API 자격 증명은 포함하지 않는다. [API 설정 안내](wiki/API_SETUP.md)에 사용 목적과 발급 경로를 설명한다. 소스 라이선스가 외부 서비스 이용 권한을 부여하지는 않는다.
