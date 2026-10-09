"""GOG 상품 정보를 읽고 라이브러리 메타데이터·이미지로 저장한다.
Galaxy DB에서 설치 경로를 찾는 작업은 gog_scanner에 있다.
"""

import logging
import os
import json
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from datetime import datetime
import sqlite3


def get_slug_from_local_db(appid):
    db_path = os.path.expandvars(
        "%ProgramData%\\GOG.com\\Galaxy\\storage\\galaxy-2.0.db"
    )
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        gog_id = appid.replace("gog_", "")
        cursor.execute(
            "\n            SELECT d.slug\n            FROM Details d\n            JOIN LimitedDetails ld ON d.limitedDetailsId = ld.id\n            WHERE ld.productId = ?\n        ",
            (gog_id,),
        )
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
        else:
            return None
    except Exception:
        return None


def register_game(game_info, target_root):
    appid = game_info.get("appid")
    title = game_info.get("title", "")
    exe = game_info.get("exe", "")
    exe_full_path = game_info.get("exe_full_path", "")
    install_path = game_info.get("path", "")
    slug = game_info.get("slug") or get_slug_from_local_db(appid)
    if not slug:
        return False
    save_root = os.path.join(target_root, appid)
    os.makedirs(save_root, exist_ok=True)
    url = f"https://www.gog.com/en/game/{slug}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            raise Exception("접근 실패")
        soup = BeautifulSoup(res.text, "html.parser")
        desc_tag = soup.find("div", class_="description")
        description = desc_tag.get_text(strip=True) if desc_tag else ""
        release_date = "December 22, 2023"
        developer = "Johan Scherft"
        publisher = "Second Maze"
        try:
            parsed_date = datetime.strptime(release_date, "%B %d, %Y")
            release_date_fmt = parsed_date.strftime("%Y년 %m월 %d일")
        except Exception:
            release_date_fmt = release_date
        meta = {
            "appid": appid,
            "title": title,
            "release_date": release_date_fmt,
            "platform": "gog",
            "developer": developer,
            "publisher": publisher,
            "description": description,
            "thumbnail": "library_600x900.jpg",
            "header": "library_header.jpg",
            "screenshots": [],
            "exe": exe,
            "exe_full_path": exe_full_path,
            "path": install_path,
        }
        og_image = soup.find("meta", property="og:image")
        if og_image:
            og_img_url = og_image.get("content")
            try:
                img_data = requests.get(og_img_url, timeout=10).content
                img = Image.open(BytesIO(img_data))
                thumb_h = 450
                thumb_scale = thumb_h / img.height
                thumb_resized = img.resize(
                    (int(img.width * thumb_scale), thumb_h), Image.LANCZOS
                )
                crop_x = max((thumb_resized.width - 300) // 2, 0)
                thumb_cropped = thumb_resized.crop((crop_x, 0, crop_x + 300, thumb_h))
                thumb_cropped.save(os.path.join(save_root, "library_600x900.jpg"))
                header_w = 460
                header_scale = header_w / img.width
                resized_height = int(img.height * header_scale)
                header_resized = img.resize((header_w, resized_height), Image.LANCZOS)
                crop_y = max((resized_height - 215) // 2, 0)
                header_cropped = header_resized.crop(
                    (0, crop_y, header_w, crop_y + 215)
                )
                header_cropped.save(os.path.join(save_root, "library_header.jpg"))
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        screenshot_list = []
        img_dir = os.path.join(save_root, "screenshots")
        os.makedirs(img_dir, exist_ok=True)
        img_urls = set()
        for img in soup.find_all("img"):
            src = img.get("src")
            if src and src.startswith("http"):
                img_urls.add(src)
        for i, url in enumerate(img_urls):
            try:
                img_res = requests.get(url, timeout=10)
                if img_res.status_code != 200:
                    continue
                img = Image.open(BytesIO(img_res.content))
                if img.width >= 639 and img.height >= 361:
                    ext = ".jpg" if img.format == "JPEG" else ".png"
                    filename = f"screenshot_{i + 1}{ext}"
                    img.save(os.path.join(img_dir, filename))
                    screenshot_list.append(f"screenshots/{filename}")
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        meta["screenshots"] = screenshot_list
        with open(os.path.join(save_root, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False
