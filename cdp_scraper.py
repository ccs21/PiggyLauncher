"""수동등록 검색과 선택 상품의 메타데이터 수집을 위한 CDP 처리.
탭 조회 → 문서 준비 대기 → 텍스트/미디어 추출 → 임시 결과 저장 흐름이다. 등록 확정은 UI에서 수행한다.
"""

import logging
from cdp_register_common import evaluate
from cdp_browser_controller import launch_browser, kill_all_cdp_chrome, kill_all_chrome
import websocket
import json
import os
import re
import time
import requests
import win32con
from PIL import Image
from io import BytesIO


def generate_login_notice_html(appid):
    html_path = os.path.abspath("cdp_login_notice.html").replace(os.sep, "/")
    html = f"""<!DOCTYPE html>\n<html lang="ko">\n<head>\n  <meta charset="UTF-8">\n  <title>로그인 필요</title>\n</head>\n<body style="font-family:sans-serif; text-align:center; padding:50px;">\n  <h2>로그인이 필요한 게임입니다</h2>\n  <p>Steam 로그인이 필요합니다.<br>아래 버튼을 눌러 로그인 페이지를 열어주세요.</p>\n  <p>로그인 후 브라우저를 건드리지 말고 가만히 두세요.<br>자동으로 등록 절차가 진행 됩니다.</p>\n  <br>\n  <button onclick="window.location.href='https://store.steampowered.com/app/{appid}/?l=koreana'"\n          style="font-size:18px; padding:10px 20px;">Steam 로그인 페이지 열기</button>\n</body>\n</html>"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    return html_path


def send_command(ws_url, method, params):
    ws = websocket.create_connection(ws_url)
    message = {"id": 1, "method": method, "params": params}
    ws.send(json.dumps(message))
    response = ws.recv()
    ws.close()
    return json.loads(response)


def scrape_steam_search_results(keyword):
    search_url = f"https://store.steampowered.com/search/?term={keyword}&ignore_preferences=1&supportedlang=koreana%2Cenglish&ndl=1&l=koreana"
    kill_all_chrome()
    kill_all_cdp_chrome()
    time.sleep(1)
    launch_browser(
        search_url, profile_name="Default", minimized=True, use_app_mode=False
    )
    tab = None
    for attempt in range(20):
        try:
            tabs = requests.get("http://localhost:9222/json").json()
            for t in tabs:
                url = t.get("url", "")
                if url.startswith("https://store.steampowered.com/search"):
                    tab = t
                    break
            if tab:
                break
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        time.sleep(0.5)
    if not tab:
        return []
    ws_url = tab["webSocketDebuggerUrl"]
    send_command(
        ws_url,
        "Network.setExtraHTTPHeaders",
        {"headers": {"Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"}},
    )
    evaluate(
        ws_url, 'Object.defineProperty(navigator, "language", { get: () => "ko-KR" });'
    )
    evaluate(
        ws_url,
        'Object.defineProperty(navigator, "languages", { get: () => ["ko-KR", "en-US"] });',
    )
    for i in range(3):
        try:
            count = evaluate(
                ws_url, 'document.querySelectorAll(".search_result_row").length'
            )
            if count and int(count) > 0:
                break
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        time.sleep(0.5)
    try:
        titles = evaluate(
            ws_url,
            '\n            [...document.querySelectorAll(".search_result_row")].map(row => {\n                const href = row.getAttribute("href") || "";\n                const titleEl = row.querySelector(".title");\n                const imgEl = row.querySelector(".search_capsule img");\n                const title = titleEl ? titleEl.textContent.trim() : "";\n                const thumb = imgEl ? imgEl.src : "";\n                const appidMatch = href.match(/\\/app\\/(\\d+)/);\n                return appidMatch ? { appid: appidMatch[1], title, thumb } : null;\n            }).filter(Boolean)\n        ',
        )
    except Exception:
        titles = []
    try:
        browser_id = tab.get("id", "")
        if browser_id:
            close_url = f"http://localhost:9222/json/close/{browser_id}"
            requests.get(close_url, timeout=2)
    except Exception as e:
        logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
    return titles


def scrape_steam_metadata(appid):
    import requests
    from cdp_register_common import get_all_tabs, is_valid_ws_url, evaluate
    from cdp_browser_controller import (
        launch_browser,
        kill_all_chrome,
        kill_all_cdp_chrome,
    )
    import win32gui
    import time
    import os

    def wait_for_game_tab(appid, timeout=60):
        deadline = time.time() + timeout
        url_prefixes = [
            f"https://store.steampowered.com/app/{appid}/",
            f"https://store.steampowered.com/agecheck/app/{appid}/",
        ]
        while time.time() < deadline:
            try:
                tabs = get_all_tabs()
                for tab in tabs:
                    ws_url = tab.get("webSocketDebuggerUrl")
                    if not is_valid_ws_url(ws_url):
                        continue
                    real_url = evaluate(ws_url, "location.href") or ""
                    if "login" in real_url.lower():
                        return "login_detected"
                    if any((real_url.startswith(prefix) for prefix in url_prefixes)):
                        return ws_url
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
            time.sleep(1)
        return None

    def get_hwnd_from_ws(ws_url):
        tabs = get_all_tabs()
        for tab in tabs:
            if tab.get("webSocketDebuggerUrl") == ws_url:
                title = tab.get("title", "")

                def enum_handler(hwnd, results):
                    if win32gui.IsWindowVisible(hwnd):
                        if title in win32gui.GetWindowText(hwnd):
                            results.append(hwnd)

                result = []
                win32gui.EnumWindows(enum_handler, result)
                return result[0] if result else None
        return None

    kill_all_chrome()
    time.sleep(1)
    url = f"https://store.steampowered.com/app/{appid}/?l=koreana"
    launch_browser(url, minimized=True)
    ws_url = wait_for_game_tab(appid)
    if ws_url == "login_detected":
        kill_all_chrome()
        time.sleep(1)
        html_path = generate_login_notice_html(appid)
        launch_browser(f"file:///{html_path}", minimized=False)
        start_time = time.time()
        while time.time() - start_time < 300:
            tmp = wait_for_game_tab(appid, timeout=5)
            if tmp and tmp != "login_detected":
                ws_url = tmp
                break
            time.sleep(1)
        if not ws_url:
            return ({}, {})
        evaluate(
            ws_url,
            "\n        (() => {\n            window.moveTo(100, 100);\n            window.resizeTo(1280, 800);\n        })()\n        ",
        )
        hwnd = get_hwnd_from_ws(ws_url)
        if hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
    elif not ws_url:
        return ({}, {})
    if "agecheck" in evaluate(ws_url, "location.href"):
        has_age_input = evaluate(ws_url, '!!document.querySelector("#ageYear")')
        if has_age_input:
            evaluate(
                ws_url,
                '\n                const y = document.querySelector("#ageYear");\n                y.value = "1990";\n                y.dispatchEvent(new Event("change"));\n            ',
            )
        evaluate(
            ws_url,
            '\n            (() => {\n                const btn = document.querySelector("#view_product_page_btn") ||\n                            document.querySelector("a.btnv6_blue_hoverfade") ||\n                            document.querySelector("input[type=\'submit\']");\n                if (btn) btn.click();\n            })()\n        ',
        )
        time.sleep(2)
    evaluate(
        ws_url,
        '\n    (() => {\n        const url = new URL(location.href);\n        if (!url.searchParams.get("l")) {\n            url.searchParams.set("l", "koreana");\n            location.href = url.toString();\n        }\n    })()\n    ',
    )
    title = evaluate(
        ws_url, 'document.querySelector(".apphub_AppName")?.textContent.trim() || ""'
    )
    description = evaluate(
        ws_url,
        'document.querySelector("#game_area_description")?.textContent.trim() || ""',
    )
    developer = evaluate(
        ws_url,
        '[...document.querySelectorAll(".dev_row")].find(row => row.querySelector(".subtitle")?.textContent.includes("개발자"))?.querySelector(".summary")?.textContent.trim() || ""',
    )
    publisher = evaluate(
        ws_url,
        '[...document.querySelectorAll(".dev_row")].find(row => row.querySelector(".subtitle")?.textContent.includes("배급사"))?.querySelector(".summary")?.textContent.trim() || ""',
    )
    release_date = evaluate(
        ws_url,
        'document.querySelector(".release_date .date")?.textContent.trim() || ""',
    )
    metadata = {
        "title": title,
        "description": description,
        "developer": developer,
        "publisher": publisher,
        "release_date": release_date,
    }
    os.makedirs("tmp_scrape", exist_ok=True)
    images = {"thumbnail": "", "header": "", "screenshots": []}

    def try_download_image(url, path):
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                with open(path, "wb") as f:
                    f.write(r.content)
                return True
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
        return False

    def wait_for_steamdb_tab(appid, timeout=30):
        deadline = time.time() + timeout
        target_prefix = f"https://steamdb.info/app/{appid}/info/"
        while time.time() < deadline:
            try:
                tabs = get_all_tabs()
                for tab in tabs:
                    ws = tab.get("webSocketDebuggerUrl")
                    if not is_valid_ws_url(ws):
                        continue
                    real_url = evaluate(ws, "location.href") or ""
                    if real_url.startswith(target_prefix):
                        return ws
            except Exception as e:
                logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
            time.sleep(0.5)
        return None

    def swap_cdn_host(url):
        if not isinstance(url, str) or not url:
            return ""
        if "shared.fastly.steamstatic.com" in url:
            return url.replace(
                "shared.fastly.steamstatic.com", "shared.akamai.steamstatic.com"
            )
        if "shared.akamai.steamstatic.com" in url:
            return url.replace(
                "shared.akamai.steamstatic.com", "shared.fastly.steamstatic.com"
            )
        return ""

    def normalize_lang_key(url):
        low = url.lower()
        if "_koreana" in low or "/koreana/" in low:
            return "koreana"
        if "_japanese" in low or "/japanese/" in low:
            return "japanese"
        if "_schinese" in low or "/schinese/" in low:
            return "schinese"
        if "_tchinese" in low or "/tchinese/" in low:
            return "tchinese"
        return "english"

    def get_lang_rank(lang):
        order = ["koreana", "english", "japanese", "schinese", "tchinese"]
        try:
            return order.index(lang)
        except ValueError:
            return 999

    def probe_image_size(url):
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200 or not r.content:
                return None
            img = Image.open(BytesIO(r.content))
            return (img.width, img.height)
        except Exception:
            return None

    def collect_steamdb_asset_urls_via_cdp():
        try:
            kill_all_cdp_chrome()
            time.sleep(1)
            info_url = f"https://steamdb.info/app/{appid}/info/"
            launch_browser(
                info_url, profile_name="Default", minimized=True, use_app_mode=False
            )
            steamdb_ws = wait_for_steamdb_tab(appid, timeout=30)
            if not steamdb_ws:
                return []
            wait_js = '\n            (() => {\n                try {\n                    const text = (document.body && document.body.innerText) ? document.body.innerText : "";\n                    const html = (document.documentElement && document.documentElement.outerHTML) ? document.documentElement.outerHTML : "";\n                    const lowText = text.toLowerCase();\n                    const lowHtml = html.toLowerCase();\n\n                    return {\n                        ready: document.readyState,\n                        textLen: text.length,\n                        hasHeaderImage: lowText.includes("header_image") || lowHtml.includes("header_image"),\n                        hasLibraryHeader: lowText.includes("library_header") || lowHtml.includes("library_header"),\n                        hasLibraryCapsule: lowText.includes("library_capsule") || lowHtml.includes("library_capsule"),\n                        hasHashLike: /[0-9a-f]{40}\\//i.test(text) || /[0-9a-f]{40}\\//i.test(html)\n                    };\n                } catch (e) {\n                    return {\n                        ready: "",\n                        textLen: 0,\n                        hasHeaderImage: false,\n                        hasLibraryHeader: false,\n                        hasLibraryCapsule: false,\n                        hasHashLike: false\n                    };\n                }\n            })()\n            '
            for i in range(20):
                state = evaluate(steamdb_ws, wait_js) or {}
                ready = state.get("ready", "")
                has_header_image = state.get("hasHeaderImage", False)
                has_library_header = state.get("hasLibraryHeader", False)
                has_library_capsule = state.get("hasLibraryCapsule", False)
                has_hash_like = state.get("hasHashLike", False)
                if ready == "complete" and (
                    has_header_image
                    or has_library_header
                    or has_library_capsule
                    or has_hash_like
                ):
                    break
                time.sleep(0.5)
            js = '\n            (() => {\n                try {\n                    const values = [];\n\n                    const push = (v) => {\n                        if (typeof v !== "string") return;\n                        v = v.trim();\n                        if (!v) return;\n                        values.push(v);\n                    };\n\n                    // 1) 실제 링크/이미지 src 수집\n                    document.querySelectorAll("a[href]").forEach(a => {\n                        push(a.href || a.getAttribute("href") || "");\n                    });\n\n                    document.querySelectorAll("img[src]").forEach(img => {\n                        push(img.src || img.getAttribute("src") || "");\n                    });\n\n                    document.querySelectorAll("source[srcset]").forEach(s => {\n                        const srcset = s.getAttribute("srcset") || "";\n                        if (!srcset) return;\n                        srcset.split(",").forEach(part => {\n                            const u = (part || "").trim().split(" ")[0];\n                            push(u);\n                        });\n                    });\n\n                    // 2) 화면 텍스트 전체\n                    push(document.body ? document.body.innerText : "");\n\n                    // 3) HTML 전체\n                    push(document.documentElement ? document.documentElement.outerHTML : "");\n\n                    return values;\n                } catch (e) {\n                    return [];\n                }\n            })()\n            '
            raw = evaluate(steamdb_ws, js) or []
            if not isinstance(raw, list):
                raw = []
            fragments = set()
            full_urls = set()
            for item in raw:
                if not isinstance(item, str) or not item.strip():
                    continue
                text = item.strip()
                for m in re.finditer("https?://[^\\s\"\\'<>]+", text, re.IGNORECASE):
                    u = m.group(0).strip()
                    low = u.lower()
                    if "store_item_assets" in low or re.search("/[0-9a-f]{40}/", low):
                        full_urls.add(u)
                for m in re.finditer(
                    "([0-9a-f]{40}/[^\\s\"\\'<>]+)", text, re.IGNORECASE
                ):
                    frag = m.group(1).strip()
                    low = frag.lower()
                    if any(
                        (
                            x in low
                            for x in [
                                "header",
                                "library_header",
                                "library_600x900",
                                "library_capsule",
                                "hero",
                                "logo",
                            ]
                        )
                    ):
                        fragments.add(frag)
            urls = set(full_urls)
            for frag in fragments:
                frag = frag.lstrip("/")
                urls.add(
                    f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{appid}/{frag}"
                )
                urls.add(
                    f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/{frag}"
                )
            urls = sorted(urls)
            return urls
        except Exception:
            return []
        finally:
            try:
                kill_all_cdp_chrome()
                time.sleep(1)
            except Exception:
                pass

    def pick_best_steamdb_asset_url(asset_urls, asset_kind):
        candidates = []
        for original_url in asset_urls:
            low = original_url.lower()
            if asset_kind == "thumbnail":
                if not ("library_600x900" in low or "library_capsule" in low):
                    continue
                if "hero" in low or "logo" in low or "header" in low:
                    continue
            elif asset_kind == "header":
                if not ("library_header" in low or "/header" in low):
                    continue
                if "hero" in low or "logo" in low:
                    continue
            else:
                continue
            lang = normalize_lang_key(original_url)
            lang_rank = get_lang_rank(lang)
            is_2x = 1 if "_2x" in low else 0
            checked_url = original_url
            size = probe_image_size(checked_url)
            if size is None:
                alt = swap_cdn_host(original_url)
                if alt:
                    alt_size = probe_image_size(alt)
                    if alt_size is not None:
                        checked_url = alt
                        size = alt_size
            if size is None:
                continue
            (w, h) = size
            ratio = w / h if h else 0
            if asset_kind == "thumbnail":
                if not (h > w and 0.55 <= ratio <= 0.75):
                    continue
                pattern_rank = 0 if "library_600x900" in low else 1
            else:
                if not (w > h and 1.8 <= ratio <= 2.4):
                    continue
                pattern_rank = 0 if "library_header" in low else 1
            score = (lang_rank, is_2x, pattern_rank, -(w * h))
            candidates.append((score, checked_url))
        if not candidates:
            return ""
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    def parse_steamdb_assets_via_cdp():
        asset_urls = collect_steamdb_asset_urls_via_cdp()
        if not asset_urls:
            return ("", "")
        header_url = pick_best_steamdb_asset_url(asset_urls, "header")
        thumb_url = pick_best_steamdb_asset_url(asset_urls, "thumbnail")
        return (header_url, thumb_url)

    steamdb_header_url = ""
    steamdb_thumb_url = ""
    steamdb_fallback_used = False
    header_path = "tmp_scrape/library_header.jpg"
    header_url_kor = (
        f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header_koreana.jpg"
    )
    header_url_eng = (
        f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg"
    )
    if try_download_image(header_url_kor, header_path):
        images["header"] = header_path
    elif try_download_image(header_url_eng, header_path):
        images["header"] = header_path
    thumb_path = "tmp_scrape/library_600x900.jpg"
    thumb_url_kor = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/library_600x900_koreana.jpg"
    thumb_url_eng = (
        f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/library_600x900.jpg"
    )
    if try_download_image(thumb_url_kor, thumb_path):
        images["thumbnail"] = thumb_path
    elif try_download_image(thumb_url_eng, thumb_path):
        images["thumbnail"] = thumb_path
    screenshot_urls = evaluate(
        ws_url,
        "\n        (() => {\n            try {\n                const urls = new Set();\n\n                // 1) data-props 기반 스크린샷 추출\n                const root = document.querySelector('.gamehighlight_desktopcarousel[data-props]') \n                           || document.querySelector('.gamehighlight_desktopcarousel');\n                if (root) {\n                    const propsStr = root.getAttribute('data-props');\n                    if (propsStr) {\n                        try {\n                            const props = JSON.parse(propsStr);\n                            const shots = props && Array.isArray(props.screenshots) ? props.screenshots : [];\n                            for (const s of shots) {\n                                if (!s) continue;\n                                const cand = s.full || s.standard || s.thumbnail;\n                                if (typeof cand === 'string' && cand) {\n                                    urls.add(cand);\n                                }\n                            }\n                        } catch (e) {\n                            // data-props JSON 파싱 실패 → 그냥 넘어가고 fallback으로 진행\n                        }\n                    }\n\n                    // 2) fallback: carousel 내부의 <img src=\"/ss_...\"> / <a href=\"...ss_...\">\n                    const imgs = Array.from(root.querySelectorAll('img[src*=\"/ss_\"]'));\n                    for (const img of imgs) {\n                        const src = img.getAttribute('src');\n                        if (typeof src === 'string' && src) {\n                            urls.add(src);\n                        }\n                    }\n\n                    const anchors = Array.from(root.querySelectorAll('a[href*=\"ss_\"]'));\n                    for (const a of anchors) {\n                        const href = a.href || a.getAttribute('href');\n                        if (typeof href === 'string' && href) {\n                            urls.add(href);\n                        }\n                    }\n                }\n\n                // 3) 최종 필터링: http(s) + 이미지 확장자\n                const exts = ['.jpg', '.jpeg', '.png', '.webp'];\n                const result = Array.from(urls).filter(href => {\n                    if (typeof href !== 'string') return false;\n                    const lower = href.toLowerCase();\n                    if (!lower.startsWith('http')) return false;\n                    return exts.some(ext => lower.includes(ext));\n                });\n\n                return result;\n            } catch (e) {\n                return [];\n            }\n        })()\n    ",
    )
    if not isinstance(screenshot_urls, list):
        screenshot_urls = []
    for i, url in enumerate(screenshot_urls):
        try:
            img = Image.open(BytesIO(requests.get(url).content))
            if img.width > 600 and img.height > 338:
                path = f"tmp_scrape/screenshot_{i + 1}.jpg"
                img.save(path)
                images["screenshots"].append(path)
        except:
            continue
    if not images["header"] or not images["thumbnail"]:
        steamdb_fallback_used = True
        (steamdb_header_url, steamdb_thumb_url) = parse_steamdb_assets_via_cdp()
    if not images["header"] and steamdb_header_url:
        if try_download_image(steamdb_header_url, header_path):
            images["header"] = header_path
    if not images["thumbnail"] and steamdb_thumb_url:
        if try_download_image(steamdb_thumb_url, thumb_path):
            images["thumbnail"] = thumb_path
    if not steamdb_fallback_used:
        try:
            tabs = get_all_tabs()
            browser_id = next(
                (t.get("id") for t in tabs if t.get("webSocketDebuggerUrl") == ws_url),
                "",
            )
            if browser_id:
                close_url = f"http://localhost:9222/json/close/{browser_id}"
                requests.get(close_url, timeout=2)
        except Exception as e:
            logging.getLogger(__name__).debug("작업 실패: %s", type(e).__name__)
    time.sleep(2)
    return (metadata, images)
