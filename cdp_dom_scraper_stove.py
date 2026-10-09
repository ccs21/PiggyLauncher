"""STOVE 상품 페이지를 로컬 Chrome CDP로 읽는 Classic 어댑터.
설치 정보 탐색과 웹 상품 페이지 해석을 분리한다. 페이지 구조가 바뀌면 이 모듈을 검토한다.
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


def run_cdp_register_stove(game: dict, target_root: str) -> bool:
    appid = game["appid"].removeprefix("stove_")
    game_url = f"https://store.onstove.com/ko/games/{appid}"
    slug = appid
    save_dir = os.path.join(target_root, slug)
    screenshot_dir = os.path.join(save_dir, "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    kill_all_chrome()
    launch_browser(game_url, minimized=True)
    ws_url = None
    for _ in range(30):
        tabs = get_all_tabs()
        for tab in tabs:
            url = tab.get("url", "")
            if f"/restrictions/agree?productNo={appid}" in url:
                ws = tab.get("webSocketDebuggerUrl")
                if is_valid_ws_url(ws):
                    try:
                        evaluate(
                            ws,
                            '\n                            const btns = Array.from(document.querySelectorAll("button"));\n                            const target = btns.find(b => b.innerText.includes("계속"));\n                            if (target) target.click();\n                        ',
                        )
                        time.sleep(2)
                    except Exception as e:
                        logging.getLogger(__name__).debug(
                            "작업 실패: %s", type(e).__name__
                        )
            elif f"/games/{appid}" in url:
                ws_url = tab.get("webSocketDebuggerUrl")
                break
        if ws_url:
            break
        time.sleep(1)
    if not is_valid_ws_url(ws_url):
        return False

    def eval_js(js_code):
        return evaluate(ws_url, js_code)

    for _ in range(20):
        try:
            loaded = eval_js(
                "\n(() => {\n  const dt = Array.from(document.querySelectorAll('dt')).some(el => el.innerText.trim() === '출시일');\n  const descReady = document.querySelector(\".inds-editor-view\")?.innerText?.trim().length > 10;\n  return dt && descReady;\n})()\n"
            )
            if loaded:
                break
        except:
            pass
        time.sleep(1)
    else:
        raise Exception("스토브 페이지 주요 구성 요소 로딩 지연")
    try:
        developer = eval_js(
            "\n(() => {\n  const dt = Array.from(document.querySelectorAll('dt')).find(el => el.innerText.trim() === '창작자');\n  return dt?.nextElementSibling?.innerText?.trim() || '';\n})()\n"
        )
        publisher = eval_js(
            "\n(() => {\n  const dt = Array.from(document.querySelectorAll('dt')).find(el => el.innerText.trim() === '배급사');\n  return dt?.nextElementSibling?.innerText?.trim() || '';\n})()\n"
        )
        release_raw = eval_js(
            "\n(() => {\n  const dt = Array.from(document.querySelectorAll('dt')).find(el => el.innerText.trim() === '출시일');\n  return dt?.nextElementSibling?.innerText?.trim() || '';\n})()\n"
        )
        release_date = ""
        try:
            (y, m, d) = release_raw.strip().split(".")
            release_date = f"{y}년 {m.zfill(2)}월 {d.zfill(2)}일"
        except:
            pass
        description = eval_js(
            'document.querySelector(".inds-editor-view")?.innerText?.trim() || ""'
        )
        meta_tags = eval_js(
            "Array.from(document.querySelectorAll('meta')).map(m => ({\n  name: m.getAttribute('name'),\n  property: m.getAttribute('property'),\n  content: m.getAttribute('content')\n}))"
        )
        og_image_url = next(
            (tag["content"] for tag in meta_tags if tag["property"] == "og:image"), None
        )
        screenshots = []
        if og_image_url:
            try:
                img_data = requests.get(og_image_url, timeout=10).content
                img = Image.open(BytesIO(img_data)).convert("RGB")
                thumb_h = 450
                thumb_scale = thumb_h / img.height
                thumb_resized = img.resize(
                    (int(img.width * thumb_scale), thumb_h), Image.LANCZOS
                )
                crop_x = max((thumb_resized.width - 300) // 2, 0)
                thumb_cropped = thumb_resized.crop((crop_x, 0, crop_x + 300, thumb_h))
                thumb_cropped.save(os.path.join(save_dir, "library_600x900.jpg"))
                header_w = 460
                header_scale = header_w / img.width
                resized_height = int(img.height * header_scale)
                header_resized = img.resize((header_w, resized_height), Image.LANCZOS)
                crop_y = max((resized_height - 215) // 2, 0)
                header_cropped = header_resized.crop(
                    (0, crop_y, header_w, crop_y + 215)
                )
                header_cropped.save(os.path.join(save_dir, "library_header.jpg"))
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        screenshot_urls = eval_js(
            "Array.from(document.querySelectorAll('img')).flatMap(img => {\n  let srcs = []\n  if (img.getAttribute('src')) srcs.push(img.getAttribute('src'))\n  if (img.getAttribute('data-src')) srcs.push(img.getAttribute('data-src'))\n  if (img.getAttribute('srcset')) {\n    const first = img.getAttribute('srcset').split(',')[0].trim().split(' ')[0]\n    if (first) srcs.push(first)\n  }\n  return srcs\n}).filter(src => src && !src.startsWith('data:'))"
        )
        count = 0
        for url in screenshot_urls:
            try:
                if url.startswith("//"):
                    url = "https:" + url
                img = Image.open(
                    BytesIO(requests.get(url, timeout=10).content)
                ).convert("RGB")
                (w, h) = img.size
                if w >= 640 and h >= 480 and (w / h <= 3.0):
                    count += 1
                    filename = f"screenshots/screenshot_{count:02}.jpg"
                    img.save(os.path.join(save_dir, filename), quality=90)
                    screenshots.append(filename)
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        meta = {
            "appid": appid,
            "title": game["title"],
            "release_date": release_date,
            "platform": "stove",
            "developer": developer,
            "publisher": publisher,
            "description": description,
            "thumbnail": "library_600x900.jpg",
            "header": "library_header.jpg",
            "screenshots": screenshots,
            "exe": game.get("exe", ""),
            "exe_full_path": f"sgup://run/{game.get('service_code', '')}",
            "path": game.get("path", ""),
        }
        with open(os.path.join(save_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False
    finally:
        kill_all_chrome()
