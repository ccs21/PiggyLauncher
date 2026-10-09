# 의존성 라이선스 확인표

2026-10-09 새 가상환경에 실제 설치한 배포판 메타데이터 및 포함 라이선스 파일 기준. 패키지는 소스 아카이브에 동봉하지 않고 pip로 별도 설치한다. 버전은 requirements-lock.txt에 고정했다.

| 패키지 | 버전 | 표시된 라이선스 | 출처 |
|---|---|---|---|
| beautifulsoup4 | 4.13.4 | MIT License | [배포판](https://pypi.org/project/beautifulsoup4/4.13.4/) |
| certifi | 2026.7.22 | MPL-2.0 | [배포판](https://pypi.org/project/certifi/2026.7.22/) |
| charset-normalizer | 3.5.2 | MIT | [배포판](https://pypi.org/project/charset-normalizer/3.5.2/) |
| comtypes | 1.4.11 | License :: OSI Approved :: MIT License | [배포판](https://pypi.org/project/comtypes/1.4.11/) |
| idna | 3.20 | BSD-3-Clause | [배포판](https://pypi.org/project/idna/3.20/) |
| pillow | 10.4.0 | HPND | [배포판](https://pypi.org/project/pillow/10.4.0/) |
| psutil | 7.0.0 | BSD-3-Clause | [배포판](https://pypi.org/project/psutil/7.0.0/) |
| pycaw | 20240210 | MIT (배포판 LICENSE 확인) | [배포판](https://pypi.org/project/pycaw/20240210/) |
| pygame | 2.6.1 | LGPL (배포판 고지 및 SDL 등 포함 구성요소 별도) | [배포판](https://pypi.org/project/pygame/2.6.1/) |
| PyGetWindow | 0.0.9 | BSD (메타데이터 표기) | [배포판](https://pypi.org/project/PyGetWindow/0.0.9/) |
| PyRect | 0.2.0 | BSD (LICENSE.txt 확인) | [배포판](https://pypi.org/project/PyRect/0.2.0/) |
| PySide6 | 6.9.0 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | [배포판](https://pypi.org/project/PySide6/6.9.0/) |
| PySide6_Addons | 6.9.0 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | [배포판](https://pypi.org/project/PySide6_Addons/6.9.0/) |
| PySide6_Essentials | 6.9.0 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | [배포판](https://pypi.org/project/PySide6_Essentials/6.9.0/) |
| pywin32 | 310 | PSF 표기 및 구성요소별 라이선스; 배포판 win32/license.txt, win32com/License.txt, adodbapi/license.txt 참조 | [배포판](https://pypi.org/project/pywin32/310/) |
| requests | 2.32.3 | Apache-2.0 | [배포판](https://pypi.org/project/requests/2.32.3/) |
| setuptools | 65.5.0 | MIT | [배포판](https://pypi.org/project/setuptools/65.5.0/) |
| shiboken6 | 6.9.0 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | [배포판](https://pypi.org/project/shiboken6/6.9.0/) |
| soupsieve | 2.10 | MIT | [배포판](https://pypi.org/project/soupsieve/2.10/) |
| typing_extensions | 4.16.0 | PSF-2.0 | [배포판](https://pypi.org/project/typing_extensions/4.16.0/) |
| urllib3 | 2.8.0 | MIT | [배포판](https://pypi.org/project/urllib3/2.8.0/) |
| websocket-client | 1.8.0 | Apache-2.0 | [배포판](https://pypi.org/project/websocket-client/1.8.0/) |
| WMI | 1.5.1 | http://www.opensource.org/licenses/mit-license.php | [배포판](https://pypi.org/project/WMI/1.5.1/) |

Qt/PySide는 선택적 라이선스와 Qt 내부 구성요소별 고지를 포함한다. 이 표를 일괄 MIT 선언으로 사용하면 안 된다. [Qt for Python 공식 고지](https://doc.qt.io/qtforpython-6/licenses.html)를 확인한다. EXE나 wheel을 재배포하는 포크는 해당 배포 형태의 고지·소스 제공·라이브러리 교체 조건을 별도로 검토해야 한다.

원본에서 가져온 Python 후보에 대해 저작권/라이선스/출처 표식과 URL을 검색하고 공개 파일 목록을 대조했다. 외부 실행 파일, 폰트, 게임 이미지, SDL 매핑 DB는 포함하지 않았다. 이 검사는 과거 코드 작성 이력을 증명하는 법적 감정은 아니다.
