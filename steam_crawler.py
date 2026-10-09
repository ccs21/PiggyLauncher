"""Steam 설치 자산과 상품 정보를 결합해 등록 파일을 만든다.
인증이 필요한 경우 작업 데이터에 표시하고 UI가 별도 브라우저 경로로 재시도한다.
"""

import logging
import os
import re
import json
import shutil
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO


def _extract_screenshot_urls_from_html(html: str):
    """
    Steam 상점 HTML에서 스크린샷 URL을 최대한 robust 하게 추출합니다.
    - 1) .gamehighlight_desktopcarousel[data-props] 의 JSON 파싱 (가장 정확)
    - 2) fallback: ss_ 패턴이 들어간 img/a의 src/href 수집
    - .jpg/.jpeg/.png/.webp 허용
    - // (protocol-relative), / (root-relative) 보정
    """
    urls = []
    seen = set()

    def add(u: str):
        if not isinstance(u, str):
            return
        u = u.strip()
        if not u:
            return
        if u.startswith("//"):
            u = "https:" + u
        elif u.startswith("/"):
            u = "https://store.steampowered.com" + u
        low = u.lower()
        if not low.startswith("http"):
            return
        exts = (".jpg", ".jpeg", ".png", ".webp")
        if not any((ext in low for ext in exts)):
            return
        if u in seen:
            return
        seen.add(u)
        urls.append(u)

    try:
        soup = BeautifulSoup(html, "html.parser")
        for el in soup.select(".gamehighlight_desktopcarousel[data-props]"):
            props_str = el.get("data-props")
            if not props_str:
                continue
            try:
                props = json.loads(props_str)
                shots = props.get("screenshots", []) if isinstance(props, dict) else []
                if isinstance(shots, list):
                    for s in shots:
                        if not isinstance(s, dict):
                            continue
                        cand = s.get("full") or s.get("standard") or s.get("thumbnail")
                        add(cand)
            except Exception:
                pass
    except Exception:
        pass
    try:
        soup = BeautifulSoup(html, "html.parser")
        for img in soup.select('img[src*="ss_"], img[data-src*="ss_"]'):
            add(img.get("src") or img.get("data-src"))
        for a in soup.select('a[href*="ss_"]'):
            add(a.get("href"))
    except Exception:
        pass
    if not urls:
        try:
            for m in re.findall(
                "(https?://[^\"\\']*ss_[^\"\\']*\\.(?:jpg|jpeg|png|webp))",
                html,
                flags=re.IGNORECASE,
            ):
                add(m)
            for m in re.findall(
                "(//[^\"\\']*ss_[^\"\\']*\\.(?:jpg|jpeg|png|webp))",
                html,
                flags=re.IGNORECASE,
            ):
                add(m)
            for m in re.findall(
                "(/[^\"\\']*ss_[^\"\\']*\\.(?:jpg|jpeg|png|webp))",
                html,
                flags=re.IGNORECASE,
            ):
                add(m)
        except Exception:
            pass
    return urls


def register_game(game_info, target_root):
    appid = str(game_info.get("appid", "")).removeprefix("steam_")
    title = game_info.get("title", "Unknown")
    steam_root = game_info.get("steam_root", "")
    exe = game_info.get("exe", "")
    exe_full_path = game_info.get("exe_full_path", "")
    path = game_info.get("path", "")
    target_dir = os.path.join(target_root, appid)
    os.makedirs(target_dir, exist_ok=True)
    try:
        cache_dir = os.path.join(steam_root, "appcache", "librarycache", appid)
        if os.path.exists(cache_dir):
            for root, _, files in os.walk(cache_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        with Image.open(file_path) as img:
                            (w, h) = img.size
                            if (w, h) == (300, 450):
                                shutil.copyfile(
                                    file_path,
                                    os.path.join(target_dir, "library_600x900.jpg"),
                                )
                            elif (w, h) == (460, 215):
                                shutil.copyfile(
                                    file_path,
                                    os.path.join(target_dir, "library_header.jpg"),
                                )
                    except Exception:
                        continue
    except Exception:
        return False
    description = ""
    developer = ""
    publisher = ""
    release_date = ""
    screenshots = []
    try:
        url = f"https://store.steampowered.com/app/{appid}/?l=koreana"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        res = requests.get(url, headers=headers, timeout=15)
        html = res.text
        if "agecheck" in res.url or "생년월일" in html:
            game_info["auth_required"] = True
            return False
        soup = BeautifulSoup(html, "html.parser")
        release_tag = soup.select_one(".release_date .date")
        release_date = release_tag.text.strip() if release_tag else ""
        desc_tag = soup.select_one("#game_area_description")
        description = desc_tag.text.strip() if desc_tag else ""
        for div in soup.select(".dev_row"):
            label = div.select_one(".subtitle")
            value = div.select_one(".summary")
            if label and value:
                lt = label.text
                if "개발자" in lt or "Developer" in lt:
                    developer = value.text.strip()
                elif "배급사" in lt or "Publisher" in lt:
                    publisher = value.text.strip()
        ss_urls = _extract_screenshot_urls_from_html(html)
        ss_dir = os.path.join(target_dir, "screenshots")
        os.makedirs(ss_dir, exist_ok=True)
        ss_urls = ss_urls[:20]
        for i, ss_url in enumerate(ss_urls):
            try:
                img_res = requests.get(ss_url, headers=headers, timeout=15)
                if img_res.status_code != 200 or not img_res.content:
                    continue
                img = Image.open(BytesIO(img_res.content))
                if img.width >= 600 and img.height >= 338:
                    file_name = f"screenshot_{i + 1}.jpg"
                    save_path = os.path.join(ss_dir, file_name)
                    img.convert("RGB").save(save_path, quality=92)
                    screenshots.append(f"screenshots/{file_name}")
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
    except Exception:
        return False
    meta = {
        "appid": int(appid),
        "title": title,
        "release_date": release_date,
        "platform": "steam",
        "developer": developer,
        "publisher": publisher,
        "description": description,
        "thumbnail": "library_600x900.jpg",
        "header": "library_header.jpg",
        "screenshots": screenshots,
        "exe": exe,
        "exe_full_path": exe_full_path,
        "path": path,
    }
    try:
        with open(os.path.join(target_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False
