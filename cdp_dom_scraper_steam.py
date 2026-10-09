"""Steam 로그인 브라우저를 이용하는 보조 수집 경로.
일반 수집으로 확보하지 못한 항목을 재시도한다. 브라우저 탭 찾기, 평가, 파일 저장을 순서대로 읽는다.
"""

import logging
import os
import json
import time
import shutil
import requests
from PIL import Image
from io import BytesIO
from cdp_register_common import get_all_tabs, is_valid_ws_url, evaluate
from cdp_browser_controller import launch_browser, kill_all_cdp_chrome, kill_all_chrome
import win32gui
import win32con


def generate_html_file(appid):
    html_path = os.path.abspath("cdp_login_notice.html").replace(os.sep, "/")
    html = f"""<!DOCTYPE html>\n<html lang="ko">\n<head>\n  <meta charset="UTF-8">\n  <title>로그인 필요</title>\n</head>\n<body style="font-family:sans-serif; text-align:center; padding:50px;">\n  <h2>로그인이 필요한 게임입니다</h2>\n  <p>Steam 로그인이 필요합니다.<br>아래 버튼을 눌러 로그인 페이지를 열어주세요.</p>\n  <p>로그인 후 브라우저를 건드리지 말고 가만히 두세요.<br>자동으로 등록 절차가 진행 됩니다.</p>\n  <br>\n  <button onclick="window.location.href='https://store.steampowered.com/app/{appid}/?l=koreana'"\n          style="font-size:18px; padding:10px 20px;">Steam 로그인 페이지 열기</button>\n</body>\n</html>"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    return html_path


def wait_for_game_tab(appid, timeout=60):
    deadline = time.time() + timeout
    url_prefixes = [
        f"https://store.steampowered.com/app/{appid}/",
        f"https://store.steampowered.com/agecheck/app/{appid}/",
    ]
    while time.time() < deadline:
        tabs = get_all_tabs()
        for tab in tabs:
            ws_url = tab.get("webSocketDebuggerUrl")
            if not is_valid_ws_url(ws_url):
                continue
            try:
                real_url = evaluate(ws_url, "location.href") or ""
                if "login" in real_url.lower():
                    return "login_detected"
                if any((real_url.startswith(prefix) for prefix in url_prefixes)):
                    return ws_url
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        time.sleep(1)
    return None


def scrape_and_register(game_info, ws_url, target_dir):

    def get_page_title(ws_url):
        js = 'document.querySelector(".apphub_AppName")?.innerText?.trim()'
        return evaluate(ws_url, js) or ""

    def get_text(selector, label):
        js = f'document.querySelector("{selector}")?.innerText?.trim()'
        value = evaluate(ws_url, js)
        return value or ""

    def get_text_by_label(keywords):
        js = f"""\n        (() => {{\n            const rows = Array.from(document.querySelectorAll("div.dev_row"));\n            for (const row of rows) {{\n                const summary = row.querySelector(".summary")?.innerText?.trim() || "";\n                const rowText = row.innerText?.toLowerCase() || "";\n                if (!summary) continue;\n                {"".join([f'if (rowText.includes("{k.lower()}")) return summary;' for k in keywords])}\n            }}\n            return "";\n        }})()\n        """
        return evaluate(ws_url, js) or ""

    def get_screenshot_urls():
        js = "\n        (() => {\n            try {\n                const urls = new Set();\n\n                // 1. data-props 기반 스크린샷 추출\n                const carousels = Array.from(\n                    document.querySelectorAll('.gamehighlight_desktopcarousel[data-props]')\n                );\n                for (const el of carousels) {\n                    const propsStr = el.getAttribute('data-props');\n                    if (!propsStr) continue;\n\n                    try {\n                        const props = JSON.parse(propsStr);\n                        const shots = props && Array.isArray(props.screenshots)\n                            ? props.screenshots\n                            : [];\n                        for (const s of shots) {\n                            if (!s) continue;\n                            const cand = s.full || s.standard || s.thumbnail;\n                            if (typeof cand === 'string' && cand) {\n                                urls.add(cand);\n                            }\n                        }\n                    } catch (e) {\n                        // JSON 파싱 실패는 무시\n                    }\n                }\n\n                // 2. fallback: carousel 영역 내 <img src=\"/ss_...\"> / <a href=\"...ss_...\">\n                if (urls.size === 0) {\n                    const root = document.querySelector('.gamehighlight_desktopcarousel') || document;\n\n                    const imgs = Array.from(root.querySelectorAll('img[src*=\"/ss_\"]'));\n                    for (const img of imgs) {\n                        const src = img.getAttribute('src');\n                        if (typeof src === 'string' && src) {\n                            urls.add(src);\n                        }\n                    }\n\n                    const anchors = Array.from(root.querySelectorAll('a[href*=\"ss_\"]'));\n                    for (const a of anchors) {\n                        const href = a.href || a.getAttribute('href');\n                        if (typeof href === 'string' && href) {\n                            urls.add(href);\n                        }\n                    }\n                }\n\n                // 3. 최종 필터링: http(s) + 이미지 확장자\n                const exts = ['.jpg', '.jpeg', '.png', '.webp'];\n                const result = Array.from(urls).filter(href => {\n                    if (typeof href !== 'string') return false;\n                    const lower = href.toLowerCase();\n                    if (!lower.startsWith('http') && !lower.startsWith('//')) return false;\n                    return exts.some(ext => lower.includes(ext));\n                });\n\n                // JS 배열 그대로 리턴 (JSON 문자열 아님)\n                return result;\n            } catch (e) {\n                return [];\n            }\n        })()\n        "
        try:
            raw = evaluate(ws_url, js)
            urls = []
            if isinstance(raw, str):
                s = raw.strip()
                if not s:
                    urls = []
                else:
                    try:
                        parsed = json.loads(s)
                        if isinstance(parsed, list):
                            urls = parsed
                        elif isinstance(parsed, str):
                            urls = [parsed]
                        else:
                            urls = []
                    except Exception:
                        urls = [s]
            elif isinstance(raw, list):
                urls = raw
            else:
                urls = []
            norm = []
            seen = set()
            exts = (".jpg", ".jpeg", ".png", ".webp")
            for u in urls:
                if not isinstance(u, str):
                    continue
                u = u.strip()
                if not u:
                    continue
                if u.startswith("//"):
                    u = "https:" + u
                elif u.startswith("/"):
                    u = "https://store.steampowered.com" + u
                low = u.lower()
                if not low.startswith("http"):
                    continue
                if not any((ext in low for ext in exts)):
                    continue
                if u in seen:
                    continue
                seen.add(u)
                norm.append(u)
            return norm
        except Exception:
            return []

    appid = str(game_info["appid"]).removeprefix("steam_")
    os.makedirs(target_dir, exist_ok=True)
    description = get_text("#game_area_description", "description")
    release_date = get_text(".release_date .date", "release_date")
    developer = get_text_by_label(["개발자", "developer"])
    publisher = get_text_by_label(["배급사", "publisher"])
    screenshots = []
    ss_dir = os.path.join(target_dir, "screenshots")
    os.makedirs(ss_dir, exist_ok=True)
    for i, url in enumerate(get_screenshot_urls()):
        try:
            res = requests.get(url, timeout=10)
            if not res.ok:
                continue
            img = Image.open(BytesIO(res.content))
            if img.width > 600 and img.height > 338:
                path = os.path.join(ss_dir, f"screenshot_{i + 1}.jpg")
                img.save(path)
                screenshots.append(f"screenshots/{os.path.basename(path)}")
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
    meta = {
        "appid": int(appid),
        "title": get_page_title(ws_url) or game_info["title"],
        "release_date": release_date,
        "platform": "steam",
        "developer": developer,
        "publisher": publisher,
        "description": description,
        "thumbnail": "library_600x900.jpg",
        "header": "library_header.jpg",
        "screenshots": screenshots,
        "exe": game_info.get("exe", ""),
        "exe_full_path": game_info.get("exe_full_path", ""),
        "path": game_info.get("path", ""),
    }
    try:
        with open(os.path.join(target_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def run_single_steam_cdp_register(
    game, target_root, theme_manager=None, parent_widget=None
):
    try:
        appid = game["appid"].removeprefix("steam_")
        game["title"]
        kill_all_chrome()
        kill_all_cdp_chrome()
        time.sleep(1)
        launch_browser(
            f"https://store.steampowered.com/app/{appid}/?l=koreana",
            headless=False,
            minimized=True,
        )
        ws_url = wait_for_game_tab(appid)
        if ws_url == "login_detected":
            kill_all_chrome()
            time.sleep(1)
            html_path = generate_html_file(appid)
            launch_browser(f"file:///{html_path}", headless=False, minimized=False)
            start_time = time.time()
            while time.time() - start_time < 300:
                tmp = wait_for_game_tab(appid, timeout=5)
                if tmp and tmp != "login_detected":
                    ws_url = tmp
                    break
                time.sleep(1)
            if not ws_url:
                return False
            evaluate(
                ws_url,
                "\n            (() => {\n                window.moveTo(100, 100);\n                window.resizeTo(1280, 800);\n            })()\n            ",
            )
            hwnd = get_hwnd_from_ws(ws_url)
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        elif not ws_url:
            return False
        if "agecheck" in evaluate(ws_url, "location.href"):
            has_age_input = evaluate(ws_url, '!!document.querySelector("#ageYear")')
            if has_age_input:
                evaluate(
                    ws_url,
                    '\n                    const y = document.querySelector("#ageYear");\n                    y.value = "1990";\n                    y.dispatchEvent(new Event("change"));\n                ',
                )
            evaluate(
                ws_url,
                '\n                (() => {\n                    const btn = document.querySelector("#view_product_page_btn") ||\n                                document.querySelector("a.btnv6_blue_hoverfade") ||\n                                document.querySelector("input[type=\'submit\']");\n                    if (btn) btn.click();\n                })()\n            ',
            )
            time.sleep(2)
        evaluate(
            ws_url,
            '\n        (() => {\n            const url = new URL(location.href);\n            if (!url.searchParams.get("l")) {\n                url.searchParams.set("l", "koreana");\n                location.href = url.toString();\n            }\n        })()\n        ',
        )
        target_dir = os.path.join(target_root, appid)
        os.makedirs(target_dir, exist_ok=True)
        success = scrape_and_register(game, ws_url, target_dir)
        if not success:
            shutil.rmtree(target_dir, ignore_errors=True)
            return False
        kill_all_chrome()
        kill_all_cdp_chrome()
        time.sleep(1)
        return True
    except Exception:
        return False


def get_hwnd_from_ws(ws_url):
    tabs = get_all_tabs()
    for tab in tabs:
        if tab.get("webSocketDebuggerUrl") == ws_url:
            title = tab.get("title", "")
            hwnd = find_window_by_title(title)
            if hwnd:
                return hwnd
    return None


def find_window_by_title(title_substring):
    hwnds = []

    def enum_handler(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            window_title = win32gui.GetWindowText(hwnd)
            if title_substring in window_title:
                hwnds.append(hwnd)

    win32gui.EnumWindows(enum_handler, None)
    return hwnds[0] if hwnds else None
