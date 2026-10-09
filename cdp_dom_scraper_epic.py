"""Epic 상품 페이지에서 DOM을 읽어 등록 정보로 변환한다.
로그인 여부와 DOM 로딩 여부는 다르며, 사이트 구조 변경에 영향을 받는 Classic 어댑터다.
"""

import logging
import os
import json
import time
import requests
from PIL import Image
from io import BytesIO
from cdp_browser_controller import launch_browser, kill_all_chrome
from cdp_register_common import get_all_tabs, evaluate, is_valid_ws_url


def run_cdp_register_epic(game, target_root):
    kill_all_chrome()
    slug = game["appid"].removeprefix("epic_")
    launch_browser(
        f"https://store.epicgames.com/ko/p/{slug}", headless=False, minimized=True
    )
    ws_url = None
    for _ in range(30):
        tabs = get_all_tabs()
        for tab in tabs:
            if slug in tab.get("url", ""):
                ws_url = tab.get("webSocketDebuggerUrl")
                break
        if ws_url:
            break
        time.sleep(1)
    if not is_valid_ws_url(ws_url):
        return
    target_dir = os.path.join(target_root, slug)
    os.makedirs(target_dir, exist_ok=True)

    def get(selector):
        return evaluate(
            ws_url, f'document.querySelector("{selector}")?.innerText?.trim() || ""'
        )

    def get_meta(property_name):
        return evaluate(
            ws_url,
            f'document.querySelector("meta[property=\\"{property_name}\\"]")?.content || ""',
        )

    title = get("h1[data-component='ProductTitle']") or game["title"]
    description = evaluate(
        ws_url,
        '\n    (() => {\n      const candidates = [\n        document.querySelector("#about-long-description"),\n        document.querySelector("div[data-testid=\'expand-collapse-content\']"),\n        document.querySelector("section[data-testid=\'product-description\']")\n      ];\n      for (const el of candidates) {\n        if (el?.innerText?.length > 200) return el.innerText.trim();\n      }\n      const all = Array.from(document.querySelectorAll("div,section,p,span"))\n        .map(e => e.innerText?.trim())\n        .filter(Boolean)\n        .sort((a, b) => b.length - a.length);\n      return all[0] || "";\n    })()\n    ',
    )
    release_date = evaluate(
        ws_url,
        '\n    (() => {\n      const els = Array.from(document.querySelectorAll("*"));\n      for (let i = 0; i < els.length - 1; i++) {\n        const label = els[i]?.innerText?.trim();\n        const raw = els[i + 1]?.innerText?.trim();\n        if (label === "출시일" && raw && raw.length < 100) {\n          const parts = raw.replaceAll(" ", "").replaceAll(".", "-").replace(/-+$/, "").split("-");\n          if (parts.length === 3) {\n            const [yy, mm, dd] = parts;\n            const yyyy = yy.length === 2 ? `20${yy}` : yy;\n            return `${yyyy}년 ${mm.padStart(2, \'0\')}월 ${dd.padStart(2, \'0\')}일`;\n          }\n        }\n      }\n      return "";\n    })()\n    ',
    )
    developer = evaluate(
        ws_url,
        '\n    (() => {\n      const els = Array.from(document.querySelectorAll("*"));\n      for (let i = 0; i < els.length - 1; i++) {\n        const label = els[i]?.innerText?.trim();\n        const value = els[i + 1]?.innerText?.trim();\n        if (label === "개발사" && value && value.length < 100) return value;\n      }\n      return "";\n    })()\n    ',
    )
    publisher = evaluate(
        ws_url,
        '\n    (() => {\n      const els = Array.from(document.querySelectorAll("*"));\n      for (let i = 0; i < els.length - 1; i++) {\n        const label = els[i]?.innerText?.trim();\n        const value = els[i + 1]?.innerText?.trim();\n        if (label === "퍼블리셔" && value && value.length < 100) return value;\n      }\n      return "";\n    })()\n    ',
    )
    image_url = get_meta("og:image")
    if image_url:
        try:
            img_data = requests.get(image_url, timeout=10).content
            img = Image.open(BytesIO(img_data))
            thumb_h = 450
            thumb_scale = thumb_h / img.height
            thumb_resized = img.resize(
                (int(img.width * thumb_scale), thumb_h), Image.LANCZOS
            )
            crop_x = max((thumb_resized.width - 300) // 2, 0)
            thumb_cropped = thumb_resized.crop((crop_x, 0, crop_x + 300, thumb_h))
            thumb_cropped.save(os.path.join(target_dir, "library_600x900.jpg"))
            header_w = 460
            header_scale = header_w / img.width
            resized_height = int(img.height * header_scale)
            header_resized = img.resize((header_w, resized_height), Image.LANCZOS)
            crop_y = max((resized_height - 215) // 2, 0)
            header_cropped = header_resized.crop((0, crop_y, header_w, crop_y + 215))
            header_cropped.save(os.path.join(target_dir, "library_header.jpg"))
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
    screenshots = []
    screenshot_dir = os.path.join(target_dir, "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    collect_script = '\n    JSON.stringify(\n        Array.from(document.querySelectorAll("img"))\n              .map(img => img.src)\n              .filter(src => src?.startsWith("http"))\n    )\n    '
    try:
        screenshot_urls = json.loads(evaluate(ws_url, collect_script))
    except:
        screenshot_urls = []
    for i, url in enumerate(screenshot_urls):
        try:
            res = requests.get(url, timeout=10)
            if not res.ok:
                continue
            img = Image.open(BytesIO(res.content))
            if img.width == 480 and img.height == 270:
                path = os.path.join(screenshot_dir, f"screenshot_{i + 1}.jpg")
                img.save(path)
                screenshots.append(f"screenshots/{os.path.basename(path)}")
        except:
            continue
    meta = {
        "appid": game["appid"].removeprefix("epic_"),
        "title": title,
        "release_date": release_date,
        "platform": "epic",
        "developer": developer,
        "publisher": publisher,
        "description": description,
        "thumbnail": "library_600x900.jpg",
        "header": "library_header.jpg",
        "screenshots": screenshots,
        "exe": game.get("exe", ""),
        "exe_full_path": game.get("exe_full_path", ""),
        "path": game.get("path", ""),
    }
    try:
        with open(os.path.join(target_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        kill_all_chrome()
        return True
    except Exception:
        kill_all_chrome()
