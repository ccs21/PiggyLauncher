# 4. GitHub 업데이트 API

## 자신의 저장소로 실습

자신의 공개 테스트 저장소에 v0.1.0 릴리즈를 만들고 무해한 텍스트 파일을 자산으로 첨부한다.

```powershell
& $python examples/release_client.py --owner YOUR_ACCOUNT --repository YOUR_REPOSITORY
```

태그와 자산 이름·크기가 나오면 조회 성공이다. 다운로드·설치·공식 런처 교체는 하지 않는다. 저장소는 필수 인수이므로 포크가 원래 제품의 릴리즈를 자동 설치하지 않는다.

요청은 GET /repos/{owner}/{repo}/releases/latest다. latest는 베타 채널 전체 목록이 아니다. 미리보기 배포에는 목록 조회와 채널 선택 규칙이 필요하다. 404는 최신 정식 릴리즈가 없는 경우에도 발생한다. 403/429는 반복 요청하지 말고 응답의 제한 정보를 확인한다. [GitHub Releases API](https://docs.github.com/en/rest/releases/releases)

## 버전·파일 선택

문자열 비교의 '0.10'과 '0.9'는 버전 의미와 다를 수 있다. 간단한 실습은 v 접두사를 제거한 정수 튜플 비교부터 시작하고, prerelease/build 표기가 필요하면 검증된 버전 라이브러리를 사용한다.

첫 자산을 무조건 선택하지 않는다. 이름·OS·CPU 규칙을 정하고 없거나 중복되면 중단한다. 자산 이름을 설치 경로에 그대로 붙이지 않는다.

## 해시 실험

```powershell
New-Item -ItemType Directory -Force lab_data | Out-Null
Set-Content lab_data/example.txt 'local update exercise'
Get-FileHash lab_data/example.txt -Algorithm SHA256
```

출력 해시를 examples.release_client.verify_file에 전달하면 True, 파일을 수정하면 False다. 자동 테스트에서 두 경우를 검증한다. 파일과 해시를 모두 공격자가 바꿀 수 있다면 해시는 배포자 인증이 되지 않는다. 서명과 신뢰 경로는 별도 문제다.

## 실제 설치기로 확장할 순서

1. 승인 또는 정해진 정책에 따라 임시 파일로 다운로드한다.
2. 크기·해시·서명을 검증한다.
3. 기존 앱을 정상 종료하고 사용자 데이터를 별도로 보존한다.
4. 검증된 새 파일을 배치한다. 압축 내부의 절대 경로·상위 경로 이동은 거부한다.
5. 실행 확인 실패 시 이전 파일로 복구한다.
6. 성공 후 백업 보관 정책을 적용한다.

교재는 3~6의 자동 실행을 포함하지 않는다. 실제 앱을 덮어쓰기 전에 가상 폴더와 실패 주입으로 상태 전이를 검증하는 것이 연습 과제다.
