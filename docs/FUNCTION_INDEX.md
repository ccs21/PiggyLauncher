# 함수별 읽기 색인

공개본의 모든 Python 함수를 AST로 목록화했다. 런처를 실행하거나 서버에 접속하지 않고 생성한다.

**참조 판정은 이름 기준의 정적 보조 정보다.** 동일한 메서드 이름이 다른 클래스에도 있을 수 있으므로 호출 가능성의 증명이 아니다. Qt 이벤트·시그널, 문자열 슬롯, 독립 실행 예제는 단순 참조 횟수만으로 삭제하지 않는다.

- 검사 파일: 68개 / 함수·메서드·중첩 함수: 646개
- 같은 스코프의 중복 정의: 0 / return·raise 뒤 명백한 도달 불가 문장: 0

행 번호는 아래 색인을 생성한 시점 기준이다. 수정 후에는 소스의 함수 이름을 기준으로 찾는다.

## auto_register_popup.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`SmartLabel.__init__`](../auto_register_popup.py) | 35–38 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`SmartLabel.mousePressEvent`](../auto_register_popup.py) | 40–43 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`SmartLabel.mouseMoveEvent`](../auto_register_popup.py) | 45–51 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`SmartLabel.mouseReleaseEvent`](../auto_register_popup.py) | 53–58 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`DraggableScrollArea.__init__`](../auto_register_popup.py) | 62–66 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`DraggableScrollArea.mousePressEvent`](../auto_register_popup.py) | 68–71 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`DraggableScrollArea.mouseMoveEvent`](../auto_register_popup.py) | 73–80 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`DraggableScrollArea.mouseReleaseEvent`](../auto_register_popup.py) | 82–84 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`AutoRegisterPopup.apply_popup_label_style`](../auto_register_popup.py) | 88–99 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`AutoRegisterPopup.apply_game_list_style`](../auto_register_popup.py) | 101–110 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`AutoRegisterPopup.__init__`](../auto_register_popup.py) | 112–118 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`AutoRegisterPopup.init_ui`](../auto_register_popup.py) | 120–189 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`AutoRegisterPopup.keyPressEvent`](../auto_register_popup.py) | 191–252 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`AutoRegisterPopup.move_focus`](../auto_register_popup.py) | 254–256 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`AutoRegisterPopup.highlight_focused_widget`](../auto_register_popup.py) | 258–283 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`AutoRegisterPopup.activate_focused_widget`](../auto_register_popup.py) | 285–304 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`AutoRegisterPopup._get_font`](../auto_register_popup.py) | 306–310 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`AutoRegisterPopup.apply_background`](../auto_register_popup.py) | 312–321 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`AutoRegisterPopup.render_results`](../auto_register_popup.py) | 323–433 | 코드 참조 있음 | 설치 검색 결과를 체크 가능한 행으로 만든다. 저장에 필요한 ID·실행 경로는 행의 속성으로 보존한다. |
| [`AutoRegisterPopup.render_results.make_toggle_handler`](../auto_register_popup.py) | 348–349 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`AutoRegisterPopup.search_installed_games`](../auto_register_popup.py) | 435–598 | 코드 참조 있음 | 선택된 플랫폼의 설치 흔적을 읽고 이미 등록된 경로를 제외한다. |
| [`AutoRegisterPopup.start_register_process`](../auto_register_popup.py) | 600–614 | 코드 참조 있음 | 사용자가 체크한 항목으로 새 등록 회차를 시작한다. 실패 집계와 완료 가드를 이전 회차에서 재사용하지 않는다. |
| [`AutoRegisterPopup.start_next_platform`](../auto_register_popup.py) | 616–653 | 코드 참조 있음 | 플랫폼별 작업을 하나씩 진행한다. 비어 있는 플랫폼은 건너뛰고 작업이 있으면 종료 신호를 연결한 뒤 시작한다. |
| [`AutoRegisterPopup.on_runner_finished`](../auto_register_popup.py) | 655–688 | 코드 참조 있음 | 이전 스레드가 완전히 끝난 뒤에만 다음 스레드로 교체한다. |
| [`AutoRegisterPopup.on_auth_required`](../auto_register_popup.py) | 690–706 | 코드 참조 있음 | 기존 스레드가 종료된 후 Steam 인증 필요 항목만 브라우저 수집기로 재시도한다. 자동 전체 재등록은 하지 않는다. |
| [`AutoRegisterPopup.on_register_complete`](../auto_register_popup.py) | 708–744 | 코드 참조 있음 | 전체 플랫폼 실패 집계를 바탕으로 결과를 알리고 라이브러리를 다시 읽는다. 마지막 플랫폼 성공만으로 전체 성공을 판단하지 않는다. |
| [`AutoRegisterPopup.on_register_complete.delayed_refresh`](../auto_register_popup.py) | 736–739 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`AutoRegisterPopup.get_checked_games`](../auto_register_popup.py) | 746–818 | 코드 참조 있음 | 체크한 행에서 플랫폼별 수집기가 기대하는 사전 구조를 만든다. 화면 제목과 플랫폼 상품 ID는 별개의 값이다. |
| [`AutoRegisterPopup.toggle_all_checkboxes`](../auto_register_popup.py) | 820–834 | 코드 참조 있음 | 전체 체크를 바꾸는 동안 개별 시그널을 막고 마지막에 전체 선택 상태를 한 번 갱신한다. |
| [`AutoRegisterPopup.update_select_all_checkbox`](../auto_register_popup.py) | 836–856 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`AutoRegisterPopup.handle_select_all_click`](../auto_register_popup.py) | 858–864 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`AutoRegisterPopup.override_select_all_click`](../auto_register_popup.py) | 866–877 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`AutoRegisterPopup.override_select_all_click.custom_mouse_press`](../auto_register_popup.py) | 868–875 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`AutoRegisterPopup.closeEvent`](../auto_register_popup.py) | 879–917 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |

## batch_setting_popup.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`BatchSettingPopup.__init__`](../batch_setting_popup.py) | 22–47 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`BatchSettingPopup.init_ui`](../batch_setting_popup.py) | 49–117 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`BatchSettingPopup.browse_program`](../batch_setting_popup.py) | 119–128 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`BatchSettingPopup.clear_program`](../batch_setting_popup.py) | 130–131 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`BatchSettingPopup.load_config`](../batch_setting_popup.py) | 133–147 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`BatchSettingPopup.save_config`](../batch_setting_popup.py) | 149–164 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`BatchSettingPopup.show_big_message`](../batch_setting_popup.py) | 166–168 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`BatchSettingPopup.closeEvent`](../batch_setting_popup.py) | 170–171 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |

## bootstrap.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`prepare_workspace`](../bootstrap.py) | 7–29 | 코드 참조 있음 | 실행 폴더에 최소 설정과 빈 라이브러리를 준비한다. |

## bottom_bar.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`BottomBar.__init__`](../bottom_bar.py) | 11–17 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`BottomBar.keyPressEvent`](../bottom_bar.py) | 19–35 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`BottomBar.eventFilter`](../bottom_bar.py) | 37–44 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`BottomBar.setup_ui`](../bottom_bar.py) | 46–86 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`BottomBar.update_view_button_icon`](../bottom_bar.py) | 88–98 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`BottomBar.toggle_view_mode`](../bottom_bar.py) | 100–106 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`BottomBar._get_font`](../bottom_bar.py) | 108–113 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`BottomBar.on_update_clicked`](../bottom_bar.py) | 115–119 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## button_mapping_popup.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`ButtonMappingPopup.__init__`](../button_mapping_popup.py) | 17–77 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`ButtonMappingPopup.show_next_prompt`](../button_mapping_popup.py) | 79–89 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`ButtonMappingPopup.check_input`](../button_mapping_popup.py) | 91–185 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`ButtonMappingPopup.save_profile`](../button_mapping_popup.py) | 187–195 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`ButtonMappingPopup.closeEvent`](../button_mapping_popup.py) | 197–203 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |

## category_select_popup.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`DraggableScrollArea.__init__`](../category_select_popup.py) | 25–30 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`DraggableScrollArea.mousePressEvent`](../category_select_popup.py) | 32–35 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`DraggableScrollArea.mouseMoveEvent`](../category_select_popup.py) | 37–42 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`DraggableScrollArea.mouseReleaseEvent`](../category_select_popup.py) | 44–46 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`CategorySelectPopup.__init__`](../category_select_popup.py) | 50–103 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`CategorySelectPopup.apply_popup_label_style`](../category_select_popup.py) | 105–116 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CategorySelectPopup.load_categories`](../category_select_popup.py) | 118–165 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CategorySelectPopup.load_categories.make_click_handler`](../category_select_popup.py) | 146–156 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CategorySelectPopup.load_categories.make_click_handler.handler`](../category_select_popup.py) | 148–154 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CategorySelectPopup.toggle_checkbox`](../category_select_popup.py) | 167–170 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CategorySelectPopup.apply_categories`](../category_select_popup.py) | 172–200 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CategorySelectPopup.update_focus`](../category_select_popup.py) | 202–224 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CategorySelectPopup.keyPressEvent`](../category_select_popup.py) | 226–242 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`CategorySelectPopup.closeEvent`](../category_select_popup.py) | 244–245 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |

## cdp_browser_controller.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`get_chrome_path`](../cdp_browser_controller.py) | 20–44 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`launch_browser`](../cdp_browser_controller.py) | 47–110 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`launch_browser.wait_and_minimize_chrome_by_pid`](../cdp_browser_controller.py) | 74–106 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`launch_browser.wait_and_minimize_chrome_by_pid.enum_handler`](../cdp_browser_controller.py) | 78–84 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`launch_browser.wait_and_minimize_chrome_by_pid.force_minimize`](../cdp_browser_controller.py) | 92–98 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`kill_all_cdp_chrome`](../cdp_browser_controller.py) | 113–133 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`kill_all_chrome`](../cdp_browser_controller.py) | 136–144 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## cdp_dom_scraper_epic.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`run_cdp_register_epic`](../cdp_dom_scraper_epic.py) | 16–128 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`run_cdp_register_epic.get`](../cdp_dom_scraper_epic.py) | 37–40 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`run_cdp_register_epic.get_meta`](../cdp_dom_scraper_epic.py) | 42–46 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## cdp_dom_scraper_steam.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`generate_html_file`](../cdp_dom_scraper_steam.py) | 19–24 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`wait_for_game_tab`](../cdp_dom_scraper_steam.py) | 27–48 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`scrape_and_register`](../cdp_dom_scraper_steam.py) | 51–157 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`scrape_and_register.get_page_title`](../cdp_dom_scraper_steam.py) | 53–55 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`scrape_and_register.get_text`](../cdp_dom_scraper_steam.py) | 57–60 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`scrape_and_register.get_text_by_label`](../cdp_dom_scraper_steam.py) | 62–64 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`scrape_and_register.get_screenshot_urls`](../cdp_dom_scraper_steam.py) | 66–114 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`run_single_steam_cdp_register`](../cdp_dom_scraper_steam.py) | 160–225 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`get_hwnd_from_ws`](../cdp_dom_scraper_steam.py) | 228–236 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`find_window_by_title`](../cdp_dom_scraper_steam.py) | 239–249 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`find_window_by_title.enum_handler`](../cdp_dom_scraper_steam.py) | 242–246 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## cdp_dom_scraper_stove.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`run_cdp_register_stove`](../cdp_dom_scraper_stove.py) | 16–156 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`run_cdp_register_stove.eval_js`](../cdp_dom_scraper_stove.py) | 52–53 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## cdp_register_common.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`get_all_tabs`](../cdp_register_common.py) | 18–30 | 코드 참조 있음 | 디버깅 포트의 탭 목록을 조회한다. Chrome이 없으면 빈 목록이다. |
| [`is_valid_ws_url`](../cdp_register_common.py) | 33–35 | 코드 참조 있음 | 탭 응답의 WebSocket 주소 형식을 확인한다. 접근 권한 검사는 아니다. |
| [`evaluate`](../cdp_register_common.py) | 38–61 | 코드 참조 있음 | JavaScript의 직렬화 가능한 결과를 반환하고 연결을 정리한다. |

## cdp_scraper.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`generate_login_notice_html`](../cdp_scraper.py) | 19–24 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`send_command`](../cdp_scraper.py) | 27–33 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`scrape_steam_search_results`](../cdp_scraper.py) | 36–97 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`scrape_steam_metadata`](../cdp_scraper.py) | 100–491 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`scrape_steam_metadata.wait_for_game_tab`](../cdp_scraper.py) | 112–133 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`scrape_steam_metadata.get_hwnd_from_ws`](../cdp_scraper.py) | 135–149 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`scrape_steam_metadata.get_hwnd_from_ws.enum_handler`](../cdp_scraper.py) | 141–144 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`scrape_steam_metadata.try_download_image`](../cdp_scraper.py) | 224–233 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`scrape_steam_metadata.wait_for_steamdb_tab`](../cdp_scraper.py) | 235–251 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`scrape_steam_metadata.swap_cdn_host`](../cdp_scraper.py) | 253–264 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`scrape_steam_metadata.normalize_lang_key`](../cdp_scraper.py) | 266–276 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`scrape_steam_metadata.get_lang_rank`](../cdp_scraper.py) | 278–283 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`scrape_steam_metadata.probe_image_size`](../cdp_scraper.py) | 285–293 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`scrape_steam_metadata.collect_steamdb_asset_urls_via_cdp`](../cdp_scraper.py) | 295–374 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`scrape_steam_metadata.pick_best_steamdb_asset_url`](../cdp_scraper.py) | 376–421 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`scrape_steam_metadata.parse_steamdb_assets_via_cdp`](../cdp_scraper.py) | 423–429 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## central_content.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`CentralContent.load_registered_games`](../central_content.py) | 27–71 | 코드 참조 있음 | 플랫폼별 meta.json을 카드용 모델로 변환한다. |
| [`CentralContent.keyPressEvent`](../central_content.py) | 75–489 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`CentralContent.keyPressEvent.try_focus`](../central_content.py) | 297–315 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CentralContent.keyPressEvent.try_focus`](../central_content.py) | 341–358 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CentralContent.keyPressEvent.try_focus_bottom`](../central_content.py) | 395–416 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CentralContent.keyPressEvent.try_focus_bottom`](../central_content.py) | 442–458 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CentralContent.eventFilter`](../central_content.py) | 491–509 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`CentralContent.mousePressEvent`](../central_content.py) | 511–516 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`CentralContent.load_categories`](../central_content.py) | 518–529 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CentralContent.__init__`](../central_content.py) | 531–573 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`CentralContent.init_ui`](../central_content.py) | 575–674 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CentralContent.force_reload_all`](../central_content.py) | 676–679 | 코드 참조 있음 | 파일을 다시 읽고 현재 카테고리를 재적용한다. 저장 직후 모델과 화면이 어긋나지 않도록 함께 갱신한다. |
| [`CentralContent.refresh_tab_bar`](../central_content.py) | 681–686 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CentralContent.on_category_changed`](../central_content.py) | 688–776 | 코드 참조 있음 | 카테고리 전환과 선택 위치 복원을 처리한다. 탭 값을 코드로 바꿀 때는 신호를 잠시 막아 재진입을 피한다. |
| [`CentralContent.on_category_changed._find_index_by`](../central_content.py) | 736–748 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CentralContent.render_cards`](../central_content.py) | 779–804 | 코드 참조 있음 | 여러 입력에서 오는 렌더 요청을 짧은 타이머로 합친다. |
| [`CentralContent._do_render_cards`](../central_content.py) | 806–969 | 코드 참조 있음 | 최신 모델을 읽고 등록·삭제·실행 복귀에 맞춰 선택 위치를 계산한다. |
| [`CentralContent._build_cards_ui`](../central_content.py) | 971–1064 | 코드 참조 있음 | 현재 표시 모델을 카드 또는 그리드 위젯으로 만든다. |
| [`CentralContent._start_fade_out`](../central_content.py) | 1066–1077 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CentralContent._start_fade_in`](../central_content.py) | 1079–1085 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CentralContent._on_fade_finished`](../central_content.py) | 1087–1098 | 코드 참조 있음 | 애니메이션 완료를 다음 렌더 상태로 연결하는 Qt 시그널 슬롯이다. 타이머와 함께 상태 전이를 읽는다. |
| [`CentralContent._recompute_visible_games_for_current_category`](../central_content.py) | 1100–1135 | 코드 참조 있음 | 전체 games에서 현재 카테고리에 해당하는 visible_games를 계산한다. 원본 목록과 화면 필터를 분리한다. |
| [`CentralContent._get_selected_card_widget`](../central_content.py) | 1137–1152 | 코드 참조 있음 | 현재 선택된(포커스된) 카드 위젯을 레이아웃에서 찾아 반환 |
| [`CentralContent.set_clicked_card`](../central_content.py) | 1154–1159 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CentralContent.get_card_style`](../central_content.py) | 1161–1169 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CentralContent.update_button_styles`](../central_content.py) | 1171–1183 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CentralContent.mouseMoveEvent`](../central_content.py) | 1185–1199 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`CentralContent.mouseReleaseEvent`](../central_content.py) | 1201–1216 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`CentralContent.on_card_click`](../central_content.py) | 1218–1271 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CentralContent.ensure_card_visible`](../central_content.py) | 1273–1290 | 코드 참조 있음 | 선택된 카드가 스크롤 영역 안에 보이도록 보정 |
| [`CentralContent.ensure_tab_visible`](../central_content.py) | 1292–1294 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CentralContent.clear_card_focus`](../central_content.py) | 1296–1299 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`CentralContent.update_info_label`](../central_content.py) | 1301–1329 | 코드 참조 있음 | 선택 게임의 메타데이터로 상단 정보를 갱신한다. 빈 목록도 처리해야 이전 게임 정보가 남지 않는다. |
| [`CentralContent._get_background_value`](../central_content.py) | 1331–1340 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## core_edit_popup.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`RomEditPopup.__init__`](../core_edit_popup.py) | 30–86 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.init_ui`](../core_edit_popup.py) | 88–169 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.init_ui.make_label`](../core_edit_popup.py) | 113–118 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.init_ui.apply_style`](../core_edit_popup.py) | 120–122 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.browse_exe`](../core_edit_popup.py) | 171–176 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.populate_core_list`](../core_edit_popup.py) | 178–194 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.on_core_changed`](../core_edit_popup.py) | 196–278 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.on_core_changed.revert`](../core_edit_popup.py) | 204–209 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.save`](../core_edit_popup.py) | 280–372 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.save.check_update`](../core_edit_popup.py) | 298–300 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.save._safe_load_json`](../core_edit_popup.py) | 304–309 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.save._norm_core_key`](../core_edit_popup.py) | 333–334 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.save._norm_path`](../core_edit_popup.py) | 336–342 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## core_installer.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`CoreDownloadWorker.__init__`](../core_installer.py) | 22–25 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`CoreDownloadWorker.run`](../core_installer.py) | 27–52 | Python/Qt 진입점 포함 | ZIP 다운로드를 먼저 시도하고 실패하면 DLL 경로를 시도한다. 결과·진행률은 Qt 시그널로 GUI에 전달한다. |
| [`CoreDownloadWorker._download_and_install`](../core_installer.py) | 54–142 | 코드 참조 있음 | 네트워크 응답을 청크 단위로 임시 파일에 저장한 후 cores 폴더에 배치한다. 메모리에 압축 파일 전체를 보관하지 않는다. |
| [`CoreInstaller.ensure_retroarch_path`](../core_installer.py) | 155–171 | 코드 참조 있음 | configs/emul_config.json에서 RetroArch 경로 확인 |
| [`CoreInstaller.normalized_core_name`](../core_installer.py) | 174–176 | 코드 참조 있음 | 표시용 코어 이름을 DLL 이름으로 정규화한다. 매핑에 없으면 입력을 그대로 사용한다. |
| [`CoreInstaller.core_dll_path`](../core_installer.py) | 179–182 | 코드 참조 있음 | 설치 루트와 정규화된 코어 이름으로 예상 DLL 위치를 계산한다. 파일을 생성하지 않는다. |
| [`CoreInstaller.is_installed`](../core_installer.py) | 185–187 | 코드 참조 있음 | 예상 DLL의 존재 여부를 확인한다. 존재 확인은 DLL의 호환성·정상 동작 검증과 다르다. |

## emulator_launcher.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`get_launcher_temp_dir`](../emulator_launcher.py) | 12–22 | 코드 참조 있음 | 런쳐 실행 폴더 기준으로 전용 임시폴더(launcher_temp)를 만들어 경로를 반환합니다. |
| [`launch_game`](../emulator_launcher.py) | 25–251 | 코드 참조 있음 | RA 또는 SA 실행 명령과 작업 폴더를 구성해 실행한다. |
| [`launch_game._clean_path_candidate`](../emulator_launcher.py) | 41–49 | 코드 참조 있음 | 로그에서 뽑은 경로 후보를 exists 검사에 적합하게 정리 |
| [`launch_game._extract_xemu_toml_path_from_log`](../emulator_launcher.py) | 51–115 | 코드 참조 있음 | xemu.log에서 xemu.toml 절대경로를 최대한 안정적으로 추출합니다. |
| [`launch_game._update_xemu_dvd_path`](../emulator_launcher.py) | 117–148 | 코드 참조 있음 | xemu.toml의 [sys.files] dvd_path를 iso_path로 갱신합니다. |
| [`launch_game.monitor_emulator_and_bat`](../emulator_launcher.py) | 184–226 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`launch_bat_after_delay`](../emulator_launcher.py) | 254–262 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## emulator_register_popup.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`DraggableScrollArea.__init__`](../emulator_register_popup.py) | 30–35 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`DraggableScrollArea.mousePressEvent`](../emulator_register_popup.py) | 37–40 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`DraggableScrollArea.mouseMoveEvent`](../emulator_register_popup.py) | 42–49 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`DraggableScrollArea.mouseReleaseEvent`](../emulator_register_popup.py) | 51–53 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`EmulatorRegisterPopup.__init__`](../emulator_register_popup.py) | 57–68 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`EmulatorRegisterPopup.init_ui`](../emulator_register_popup.py) | 70–129 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`EmulatorRegisterPopup.build_right_section`](../emulator_register_popup.py) | 131–246 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`EmulatorRegisterPopup.select_rom_folder`](../emulator_register_popup.py) | 248–251 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`EmulatorRegisterPopup.build_left_section`](../emulator_register_popup.py) | 253–335 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`EmulatorRegisterPopup.select_emulator_path`](../emulator_register_popup.py) | 337–343 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`EmulatorRegisterPopup.clear_emulator_path`](../emulator_register_popup.py) | 345–347 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`EmulatorRegisterPopup._get_font`](../emulator_register_popup.py) | 349–354 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`EmulatorRegisterPopup.save_left_config_and_refresh_right`](../emulator_register_popup.py) | 356–377 | 코드 참조 있음 | 실행기 경로를 저장한 뒤 사용 가능한 코어 선택지를 다시 만든다. 실행기 설정과 기종 설정의 의존 관계를 보여준다. |
| [`EmulatorRegisterPopup.clear_right_layout`](../emulator_register_popup.py) | 379–384 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`EmulatorRegisterPopup.save_right_config_to_meta`](../emulator_register_popup.py) | 386–680 | 코드 참조 있음 | 기종별 대표 코어·ROM 폴더를 카드 메타데이터로 저장한다. 기종별 디렉터리형 ROM 처리는 일반 확장자 처리와 분기된다. |
| [`EmulatorRegisterPopup.save_right_config_to_meta.scan_for_eboot`](../emulator_register_popup.py) | 534–550 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`EmulatorRegisterPopup.save_right_config_to_meta.delayed_refresh`](../emulator_register_popup.py) | 674–677 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`EmulatorRegisterPopup.cleanup`](../emulator_register_popup.py) | 682–694 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`EmulatorRegisterPopup.closeEvent`](../emulator_register_popup.py) | 696–698 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`EmulatorRegisterPopup.reject`](../emulator_register_popup.py) | 700–702 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`EmulatorRegisterPopup._on_system_core_selected`](../emulator_register_popup.py) | 704–785 | 코드 참조 있음 | 코어 선택을 검증하고 필요한 다운로드를 요청한다. 되돌리기 중에는 가드를 세워 선택 변경 신호의 재진입을 막는다. |
| [`EmulatorRegisterPopup._on_system_core_selected.revert`](../emulator_register_popup.py) | 713–718 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## epic_scanner.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`normalize_title`](../epic_scanner.py) | 12–20 | 코드 참조 있음 | 제목 비교를 방해하는 가격·안내 문구를 제거한다. 상품 고유 ID 조회를 대신하는 완전한 식별 방법은 아니다. |
| [`load_slug_map`](../epic_scanner.py) | 23–35 | 코드 참조 있음 | 사용자가 설정한 매핑 JSON을 읽는다. 주소가 비어 있으면 빈 목록을 반환하고 통신하지 않는다. |
| [`find_slug`](../epic_scanner.py) | 38–49 | 코드 참조 있음 | 정규화된 제목의 정확 일치를 우선하고 부분 일치를 보조로 사용한다. 동명 상품은 잘못 매칭될 수 있다. |
| [`scan_epic_games`](../epic_scanner.py) | 52–82 | 코드 참조 있음 | 로컬 .item 설치 매니페스트와 선택적 slug 매핑을 결합한다. 구입 목록 전체가 아니라 설치 흔적을 읽는다. |

## examples/lab_client.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`NoticeInbox.__init__`](../examples/lab_client.py) | 9–11 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`NoticeInbox.ingest`](../examples/lab_client.py) | 13–18 | 코드 참조 있음 | 순서대로 큐에 넣는다. 같은 응답을 다시 받아도 중복 추가하지 않는다. |
| [`main`](../examples/lab_client.py) | 21–40 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## examples/lab_server.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`LabState.__init__`](../examples/lab_server.py) | 18–26 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`LabState.login`](../examples/lab_server.py) | 28–38 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`LabState.valid`](../examples/lab_server.py) | 40–42 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`LabState.logout`](../examples/lab_server.py) | 44–46 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`handler_for`](../examples/lab_server.py) | 49–117 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`handler_for.Handler.log_message`](../examples/lab_server.py) | 51–53 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`handler_for.Handler.reply`](../examples/lab_server.py) | 55–62 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`handler_for.Handler.do_POST`](../examples/lab_server.py) | 64–90 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`handler_for.Handler.do_GET`](../examples/lab_server.py) | 92–115 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`main`](../examples/lab_server.py) | 120–135 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## examples/notice_store.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`NoticeStore.__init__`](../examples/notice_store.py) | 9–13 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`NoticeStore.append`](../examples/notice_store.py) | 15–21 | 코드 참조 있음 | 추가만 허용한다. 순번을 재사용하지 않아 커서 뒤의 공지를 놓치지 않는다. |
| [`NoticeStore.page`](../examples/notice_store.py) | 23–29 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`NoticeStore.backup`](../examples/notice_store.py) | 31–37 | 코드 참조 있음 | SQLite backup API는 열린 DB도 일관된 사본으로 복사한다. 기존 파일은 덮어쓰지 않는다. |
| [`main`](../examples/notice_store.py) | 40–62 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## examples/notice_sync.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`DurableInbox.__init__`](../examples/notice_sync.py) | 9–15 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`DurableInbox._save`](../examples/notice_sync.py) | 17–25 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`DurableInbox.ingest`](../examples/notice_sync.py) | 27–39 | 코드 참조 있음 | 커서와 큐를 한 파일에 확정한다. 커서만 앞서 저장하면 알림이 유실된다. |
| [`DurableInbox.acknowledge_first`](../examples/notice_sync.py) | 41–44 | 코드 참조 있음 | 실제로 표시한 뒤 호출한다. 표시 직후 전원 차단 시 중복은 가능하나 유실은 피한다. |
| [`synchronize`](../examples/notice_sync.py) | 47–58 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`main`](../examples/notice_sync.py) | 61–69 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## examples/oauth_desktop.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`authorization_request`](../examples/oauth_desktop.py) | 16–40 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`exchange_code`](../examples/oauth_desktop.py) | 43–69 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## examples/release_client.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`latest_release`](../examples/release_client.py) | 11–21 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`verify_file`](../examples/release_client.py) | 24–32 | 코드 참조 있음 | 신뢰한 별도 경로에서 받은 SHA-256과 비교한다. 해시는 서명이 아니다. |

## examples/smtp_optional.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`make_message`](../examples/smtp_optional.py) | 10–18 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`send_example`](../examples/smtp_optional.py) | 21–32 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## game_detail_screen.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`DraggableScrollArea.__init__`](../game_detail_screen.py) | 42–45 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`DraggableScrollArea.mousePressEvent`](../game_detail_screen.py) | 47–50 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`DraggableScrollArea.mouseMoveEvent`](../game_detail_screen.py) | 52–59 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`DraggableScrollArea.mouseReleaseEvent`](../game_detail_screen.py) | 61–63 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`GameDetailScreen.__init__`](../game_detail_screen.py) | 71–86 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`GameDetailScreen.init_ui`](../game_detail_screen.py) | 88–139 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameDetailScreen.resize_sections`](../game_detail_screen.py) | 141–405 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameDetailScreen.resize_sections.create_icon_button`](../game_detail_screen.py) | 243–259 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameDetailScreen.resize_sections.make_meta_label`](../game_detail_screen.py) | 393–399 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameDetailScreen.keyPressEvent`](../game_detail_screen.py) | 407–426 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`GameDetailScreen.get_random_screenshot_path`](../game_detail_screen.py) | 428–444 | 코드 참조 있음 | 스크린샷 후보에서 표시할 이미지를 고른다. 후보가 없을 때의 기본 배경 처리는 호출부가 담당한다. |
| [`GameDetailScreen.setup_top_section`](../game_detail_screen.py) | 446–574 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameDetailScreen.resizeEvent`](../game_detail_screen.py) | 576–578 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`GameDetailScreen.clean_up_empty_labels`](../game_detail_screen.py) | 580–593 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameDetailScreen.run_game`](../game_detail_screen.py) | 595–802 | 코드 참조 있음 | 프리셋 적용 → 실행 → 시작 안정화 확인 → 종료 감시 순서로 진행한다. |
| [`GameDetailScreen.run_game.wait_and_then_monitor`](../game_detail_screen.py) | 688–797 | 코드 참조 있음 | 처음 뜬 프로세스를 곧바로 시작 확정으로 보지 않는다. |
| [`GameDetailScreen.wait_all`](../game_detail_screen.py) | 804–867 | 코드 참조 있음 | 실행 게임과 연동 프로그램 이름을 모아 생존 여부를 반복 확인한다. |
| [`GameDetailScreen.restore_launcher`](../game_detail_screen.py) | 869–871 | 코드 참조 있음 | 감시 스레드에서 복귀를 요청한다. 위젯은 이 함수에서 직접 조작하지 않는다. |
| [`GameDetailScreen._restore_launcher_ui`](../game_detail_screen.py) | 874–901 | 코드 참조 있음 | GUI 스레드에서 설정·화면·입력·알림을 순서대로 복구한다. |
| [`GameDetailScreen._reattach_ui`](../game_detail_screen.py) | 904–910 | 코드 참조 있음 | 늦게 시작된 게임을 발견했을 때 GUI 측 실행 상태를 다시 잠근다. |
| [`GameDetailScreen._any_window_with_keywords`](../game_detail_screen.py) | 912–982 | 코드 참조 있음 | 키워드 리스트 중 하나라도 포함된 '인증/업데이트/VR 안내' 보이는 최상위 창이 있으면 True. |
| [`GameDetailScreen._any_window_with_keywords.callback`](../game_detail_screen.py) | 948–976 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameDetailScreen._is_auth_or_update_active`](../game_detail_screen.py) | 984–1037 | 코드 참조 있음 | 스팀/에픽 로그인/2FA/업데이트/검증/클라우드 동기화/VR 안내 등 단계 감지 |
| [`GameDetailScreen._start_post_restore_watchdog`](../game_detail_screen.py) | 1039–1076 | 코드 참조 있음 | 복귀 후 일정 시간 감시하다가 뒤늦게 게임이 뜨면 |
| [`GameDetailScreen._start_post_restore_watchdog.watchdog`](../game_detail_screen.py) | 1048–1074 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameDetailScreen._monitor_reattached_game_until_exit`](../game_detail_screen.py) | 1078–1120 | 코드 참조 있음 | 워치독이 뒤늦게 실행된 게임에 재부착한 뒤: |
| [`GameDetailScreen.open_graphic_setting`](../game_detail_screen.py) | 1122–1126 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameDetailScreen.open_batch_setting`](../game_detail_screen.py) | 1128–1130 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameDetailScreen.on_delete_clicked`](../game_detail_screen.py) | 1132–1160 | 코드 참조 있음 | 삭제 확인 후 등록 데이터를 지우고 메인 목록을 갱신한다. 게임 설치 폴더 삭제와 혼동하지 않도록 경로를 읽는다. |
| [`GameDetailScreen.on_delete_clicked.delayed_refresh`](../game_detail_screen.py) | 1152–1155 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameDetailScreen.open_category_popup`](../game_detail_screen.py) | 1162–1166 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameDetailScreen.open_edit_popup`](../game_detail_screen.py) | 1168–1188 | 코드 참조 있음 | 현재 메타데이터를 편집 화면에 넘긴다. 저장은 편집 화면의 명시적 등록/수정 동작에서 이루어진다. |
| [`GameDetailScreen.closeEvent`](../game_detail_screen.py) | 1190–1220 | Python/Qt 진입점 포함 | 이미지·애니메이션 참조를 해제하는 Qt 종료 콜백이다. 감시 스레드가 사용하는 게임 식별 정보는 유지한다. |

## gamepad_config_popup.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`GamepadConfigPopup.__init__`](../gamepad_config_popup.py) | 13–51 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`GamepadConfigPopup.check_inputs`](../gamepad_config_popup.py) | 53–65 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## gamepad_handler.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`GamepadHandler.__init__`](../gamepad_handler.py) | 28–70 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`GamepadHandler._reset_input_states`](../gamepad_handler.py) | 72–80 | 코드 참조 있음 | [추가] 홀드/연타 잔상 제거용 입력 상태 초기화 |
| [`GamepadHandler._enter_drop_window`](../gamepad_handler.py) | 82–84 | 코드 참조 있음 | [추가] 차단 해제 직후 완전 드랍 구간 진입(단발 포함) |
| [`GamepadHandler._in_drop_window`](../gamepad_handler.py) | 86–88 | 코드 참조 있음 | [추가] 차단 해제 직후 완전 드랍 구간인지 |
| [`GamepadHandler._should_drop_input_now`](../gamepad_handler.py) | 90–92 | 코드 참조 있음 | [추가] '차단'이 아니더라도, 드랍 구간이면 입력을 무조건 무시 |
| [`GamepadHandler._now`](../gamepad_handler.py) | 94–95 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GamepadHandler._enter_protect_window`](../gamepad_handler.py) | 97–98 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GamepadHandler._in_protect_window`](../gamepad_handler.py) | 100–101 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GamepadHandler.load_profiles`](../gamepad_handler.py) | 103–107 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GamepadHandler.reload_profiles`](../gamepad_handler.py) | 109–114 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GamepadHandler.refresh_gamepads`](../gamepad_handler.py) | 116–159 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GamepadHandler.poll_inputs`](../gamepad_handler.py) | 161–260 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GamepadHandler._process_hold_and_fire`](../gamepad_handler.py) | 262–316 | 코드 참조 있음 | 논리 입력(버튼/방향)에 대해: |
| [`GamepadHandler.poll_pygame_events`](../gamepad_handler.py) | 318–363 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GamepadHandler._fire_key`](../gamepad_handler.py) | 365–377 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GamepadHandler._get_base_block_reason`](../gamepad_handler.py) | 379–396 | 코드 참조 있음 | BASE 차단 사유 문자열을 반환합니다. (로그용) |
| [`GamepadHandler._should_block_input`](../gamepad_handler.py) | 398–422 | 코드 참조 있음 | 런처 창이 최소화되어 있거나, 실행 중인 게임을 감시하는 동안에는 |
| [`GamepadHandler._is_launcher_foreground`](../gamepad_handler.py) | 424–454 | 코드 참조 있음 | 런쳐가 '포그라운드'인지 판정 (팝업/다이얼로그 포함) |
| [`GamepadHandler._watch_block_state`](../gamepad_handler.py) | 456–490 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GamepadHandler._apply_polling_state`](../gamepad_handler.py) | 492–516 | 코드 참조 있음 | blocking=True  => 입력 관련 폴링 타이머 정지 |
| [`GamepadHandler.pause_input`](../gamepad_handler.py) | 518–525 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GamepadHandler.get_topmost_visible_window`](../gamepad_handler.py) | 527–537 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GamepadHandler.set_hhc_mode`](../gamepad_handler.py) | 539–544 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GamepadHandler.eventFilter`](../gamepad_handler.py) | 546–581 | Python/Qt 진입점 포함 | 런처가 '블록 조건'일 때(= 현재 구조상 최소화 상태일 때), |

## gamepad_manager.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`load_profiles`](../gamepad_manager.py) | 12–16 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`get_unmapped_gamepads`](../gamepad_manager.py) | 19–32 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## gog_crawler.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`get_slug_from_local_db`](../gog_crawler.py) | 16–37 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`register_game`](../gog_crawler.py) | 40–134 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## gog_scanner.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`get_db_path`](../gog_scanner.py) | 11–17 | 코드 참조 있음 | Galaxy의 로컬 DB 기본 경로를 확인한다. DB가 없으면 None이며 스캐너는 별도 DB를 만들어서는 안 된다. |
| [`scan_gog_installed_games`](../gog_scanner.py) | 20–50 | 코드 참조 있음 | Galaxy 설치 테이블에서 제목·실행 파일·설치 폴더를 읽는다. 플랫폼 DB 구조에 의존하는 어댑터다. |
| [`main`](../gog_scanner.py) | 53–58 | 코드 참조 있음 | 스캐너만 실행할 때의 진입점이다. 런처 UI를 띄우지 않고 로컬 설치 검색을 수행한다. |

## graphic_setting_popup.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`GraphicSettingPopup.__init__`](../graphic_setting_popup.py) | 30–59 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`GraphicSettingPopup.init_ui`](../graphic_setting_popup.py) | 61–260 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GraphicSettingPopup.init_ui.apply_fontcolor`](../graphic_setting_popup.py) | 70–71 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GraphicSettingPopup.init_ui.browse_locale_path`](../graphic_setting_popup.py) | 213–220 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GraphicSettingPopup.defer_monitor_log`](../graphic_setting_popup.py) | 262–279 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GraphicSettingPopup.load_preset`](../graphic_setting_popup.py) | 281–292 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GraphicSettingPopup.apply_preset`](../graphic_setting_popup.py) | 294–323 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GraphicSettingPopup.save_preset`](../graphic_setting_popup.py) | 325–357 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GraphicSettingPopup.update_resolution_combo`](../graphic_setting_popup.py) | 359–372 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GraphicSettingPopup.update_rate_combo`](../graphic_setting_popup.py) | 374–382 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`get_current_monitor_id`](../graphic_setting_popup.py) | 385–401 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## main.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`check_chrome_installed`](../main.py) | 30–53 | 코드 참조 있음 | PATH와 Windows 등록 경로에서 Chrome 실행 파일을 찾는다. 설치나 다운로드는 하지 않는다. |
| [`get_current_monitor_id`](../main.py) | 59–76 | 코드 참조 있음 | Win32 모니터 핸들을 디스플레이 이름으로 바꾼다. ctypes 구조체 필드 순서는 Windows ABI와 같아야 한다. |
| [`get_monitor_scale`](../main.py) | 79–95 | 코드 참조 있음 | 창이 속한 모니터의 DPI를 읽어 배율로 바꾼다. API 사용 불가 시 기본 배율을 사용한다. |
| [`get_monitor_resolution`](../main.py) | 98–105 | 코드 참조 있음 | 작업 표시줄을 뺀 작업 영역이 아닌 모니터 전체 사각형에서 너비·높이를 얻는다. |
| [`SplashWindow.__init__`](../main.py) | 109–118 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`SplashWindow.resizeEvent`](../main.py) | 120–122 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`PiggyLauncher.__init__`](../main.py) | 126–143 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`PiggyLauncher.init_ui`](../main.py) | 145–164 | 코드 참조 있음 | 상단·중앙·하단 위젯을 조립하고 서로의 탐색 대상을 연결한다. 각 위젯의 소유자는 메인 창이다. |
| [`PiggyLauncher.start_gamepad_handling`](../main.py) | 166–175 | 코드 참조 있음 | 패드 입력 처리기와 신규 연결 확인 타이머를 준비한다. GUI 수명과 입력 처리기의 수명을 맞춘다. |
| [`PiggyLauncher.on_guid_selected`](../main.py) | 177–181 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`PiggyLauncher.start_mapping_for_new_pads`](../main.py) | 183–268 | 코드 참조 있음 | 신규 연결 패드 처리: |
| [`PiggyLauncher.check_new_gamepads`](../main.py) | 270–279 | 코드 참조 있음 | 연결된 GUID를 저장된 매핑과 비교한다. 제품명만 같아도 GUID가 다를 수 있어 이름만으로 합치지 않는다. |
| [`PiggyLauncher.changeEvent`](../main.py) | 281–302 | Python/Qt 진입점 포함 | 창 상태 변경을 받는 Qt 콜백이다. 직접 호출 참조가 없어도 Qt가 호출하므로 삭제 대상이 아니다. |
| [`PiggyLauncher.changeEvent._resume_notifications`](../main.py) | 294–300 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`show_launcher`](../main.py) | 371–387 | 코드 참조 있음 | 시작 안내 이후 메인 창을 만들고 전역 참조로 유지한다. 지역 변수만 남기면 창 수명이 끝날 수 있다. |

## notification_manager.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`load_noti_history`](../notification_manager.py) | 15–23 | 코드 참조 있음 | 저장된 수신 이력을 읽는다. 파일 없음과 읽기 실패에는 빈 목록을 반환한다. |
| [`save_noti_history`](../notification_manager.py) | 26–32 | 코드 참조 있음 | 수신 이력을 저장한다. 팝업 큐는 메모리 상태이며 이 파일과 수명이 다르다. |
| [`NotificationManager.__init__`](../notification_manager.py) | 36–42 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`NotificationManager.pause`](../notification_manager.py) | 44–46 | 코드 참조 있음 | 게임 시작 직전 호출: 팝업/소리 대기 |
| [`NotificationManager.resume`](../notification_manager.py) | 48–52 | 코드 참조 있음 | 게임 종료 직후 호출: 집계 플러시 후 큐 재개 |
| [`NotificationManager.push`](../notification_manager.py) | 54–104 | 코드 참조 있음 | :param message: 표시할 메시지(예: "게임패드 XXX 연결됨") |
| [`NotificationManager._play_notify_sound_async`](../notification_manager.py) | 106–123 | 코드 참조 있음 | paused가 False일 때만 알림음을 비동기 재생 |
| [`NotificationManager._play_notify_sound_async.play_notify_sound`](../notification_manager.py) | 111–121 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`NotificationManager._try_show_next`](../notification_manager.py) | 125–136 | 코드 참조 있음 | GUI 스레드에서 한 건만 표시한다. 팝업의 실제 종료 신호로 다음 건을 연다. |
| [`NotificationManager._on_popup_closed`](../notification_manager.py) | 138–141 | 코드 참조 있음 | 표시 시간과 큐 타이머가 어긋나 알림이 겹치지 않도록 완료를 전달받는다. |
| [`NotificationManager._aggregate_gamepad`](../notification_manager.py) | 143–151 | 코드 참조 있음 | 게임 중 들어온 게임패드 노티를 큐에 넣지 않고 집계 버퍼로만 누적 |
| [`NotificationManager._flush_gamepad_buffer`](../notification_manager.py) | 153–168 | 코드 참조 있음 | resume 시 호출: 집계된 게임패드 노티를 요약 규칙으로 0~1건 표출 |
| [`NotificationManager._reset_gamepad_buffer`](../notification_manager.py) | 170–174 | 코드 참조 있음 | 게임 중 집계한 패드 변화 횟수와 마지막 상태를 함께 비운다. |
| [`NotificationManager._parse_gamepad_message`](../notification_manager.py) | 176–193 | 코드 참조 있음 | 메시지가 게임패드 연결/해제 알림인지 판별하고 (is_gamepad, name, state)를 반환. |

## notification_popup.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`NotificationPopup.__init__`](../notification_popup.py) | 15–50 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`NotificationPopup.fade_out`](../notification_popup.py) | 52–60 | 코드 참조 있음 | 표시 시간이 끝나면 투명도를 줄인다. 실제 종료가 큐의 다음 항목을 깨운다. |
| [`NotificationPopup.mousePressEvent`](../notification_popup.py) | 62–68 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`NotificationPopup.closeEvent`](../notification_popup.py) | 70–76 | Python/Qt 진입점 포함 | 시간 경과와 클릭 모두 동일한 완료 신호를 한 번만 보낸다. |

## our_gamepad_db.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`_load_file`](../our_gamepad_db.py) | 15–22 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`load`](../our_gamepad_db.py) | 25–35 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`lookup`](../our_gamepad_db.py) | 38–43 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## popup_alert.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`CustomAlertDialog.__init__`](../popup_alert.py) | 11–69 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`CustomAlertDialog.keyPressEvent`](../popup_alert.py) | 71–78 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |

## popup_loading_launcher.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`launch_popup_with_loading`](../popup_loading_launcher.py) | 10–57 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`launch_popup_with_loading.run_popup`](../popup_loading_launcher.py) | 47–55 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## popup_utils.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`ConfirmDialog.__init__`](../popup_utils.py) | 18–91 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`ConfirmDialog.update_button_styles`](../popup_utils.py) | 93–101 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`ConfirmDialog.keyPressEvent`](../popup_utils.py) | 103–116 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`ProgressDialog.__init__`](../popup_utils.py) | 132–189 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`ProgressDialog.set_message`](../popup_utils.py) | 191–192 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`ProgressDialog.set_indeterminate`](../popup_utils.py) | 194–198 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`ProgressDialog.set_progress`](../popup_utils.py) | 200–210 | 코드 참조 있음 | value가 None이면 indeterminate 유지 |
| [`ProgressDialog.enable_close`](../popup_utils.py) | 212–217 | 코드 참조 있음 | 작업 완료 후 닫기 허용/버튼 표시 |
| [`ProgressDialog.closeEvent`](../popup_utils.py) | 219–223 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`ProgressDialog.keyPressEvent`](../popup_utils.py) | 225–229 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`ProgressDialog.connect_worker`](../popup_utils.py) | 231–249 | 코드 참조 있음 | worker는 다음 시그널을 가질 수 있습니다(존재하는 것만 연결): |
| [`ProgressDialog._on_worker_progress`](../popup_utils.py) | 252–253 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`ProgressDialog._on_worker_status`](../popup_utils.py) | 256–257 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`ProgressDialog._on_worker_indeterminate`](../popup_utils.py) | 260–261 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`ProgressDialog._on_worker_done_ok`](../popup_utils.py) | 264–268 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`ProgressDialog._on_worker_done_error`](../popup_utils.py) | 271–273 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## popup_windows.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`BasePopup.__init__`](../popup_windows.py) | 16–26 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`BasePopup.init_ui`](../popup_windows.py) | 28–87 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`BasePopup.resize_popup`](../popup_windows.py) | 89–96 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## register_progress_popup.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`RegisterProgressPopup.__init__`](../register_progress_popup.py) | 11–52 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`RegisterProgressPopup.set_text`](../register_progress_popup.py) | 54–55 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RegisterProgressPopup.closeEvent`](../register_progress_popup.py) | 57–67 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |

## register_thread.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`RegisterThread.__init__`](../register_thread.py) | 17–28 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`RegisterThread.run`](../register_thread.py) | 30–59 | Python/Qt 진입점 포함 | 개별 실패를 기록하고 다음 게임을 계속 처리한다. |
| [`RegisterThread.get_auth_queue`](../register_thread.py) | 61–63 | 코드 참조 있음 | 종료된 작업의 인증 대상을 복사해 반환한다. 내부 목록은 외부가 수정하지 않는다. |

## rom_edit_popup.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`RomEditPopup.__init__`](../rom_edit_popup.py) | 36–97 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.init_ui`](../rom_edit_popup.py) | 99–247 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.init_ui.make_label`](../rom_edit_popup.py) | 126–131 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.init_ui.apply_style`](../rom_edit_popup.py) | 133–135 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.browse_bat_file`](../rom_edit_popup.py) | 249–257 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.clear_bat_path`](../rom_edit_popup.py) | 259–260 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.scrap_single_game`](../rom_edit_popup.py) | 262–405 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.scrap_single_game.sanitize_filename`](../rom_edit_popup.py) | 319–320 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.scrap_single_game.save_image`](../rom_edit_popup.py) | 384–391 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.populate_core_list`](../rom_edit_popup.py) | 407–424 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.browse_exe`](../rom_edit_popup.py) | 426–431 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.browse_title_image`](../rom_edit_popup.py) | 433–438 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.browse_screenshot`](../rom_edit_popup.py) | 440–445 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.on_core_changed`](../rom_edit_popup.py) | 447–529 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.on_core_changed.revert`](../rom_edit_popup.py) | 455–460 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.save`](../rom_edit_popup.py) | 531–663 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.save.check_update`](../rom_edit_popup.py) | 555–557 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.save._safe_load_json`](../rom_edit_popup.py) | 562–567 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.save._norm_core_key`](../rom_edit_popup.py) | 591–592 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.save._norm_path`](../rom_edit_popup.py) | 594–600 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomEditPopup.save.sanitize_filename`](../rom_edit_popup.py) | 620–621 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## rom_list_core_cleaner.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`_log`](../rom_list_core_cleaner.py) | 28–30 | 코드 참조 있음 | 로컬 정리 작업의 진단을 DEBUG 수준에 남긴다. 네트워크 보고는 하지 않는다. |
| [`_normalize_path`](../rom_list_core_cleaner.py) | 33–37 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`_safe_load_json`](../rom_list_core_cleaner.py) | 40–46 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`_atomic_write_json`](../rom_list_core_cleaner.py) | 49–53 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`_collect_all_string_values`](../rom_list_core_cleaner.py) | 56–72 | 코드 참조 있음 | configs/emul_config.json에서 '실행기 경로'를 특정 키에 한정하지 않고 |
| [`_load_emul_config_paths`](../rom_list_core_cleaner.py) | 75–95 | 코드 참조 있음 | emul_config.json에서 실행 경로 후보들을 수집하고 정규화하여 반환 |
| [`_read_meta_main_core`](../rom_list_core_cleaner.py) | 98–112 | 코드 참조 있음 | meta.json에서 main_core, main_core_type을 읽어 반환. |
| [`_process_one_emul_dir`](../rom_list_core_cleaner.py) | 115–165 | 코드 참조 있음 | 단일 기종 폴더 처리: |
| [`_sweep_tmp_files`](../rom_list_core_cleaner.py) | 168–180 | 코드 참조 있음 | _atomic_write_json() 도중 예외 등으로 남았을 수 있는 rom_list.json.tmp를 정리한다. |
| [`_cleanup_after_run`](../rom_list_core_cleaner.py) | 183–199 | 코드 참조 있음 | 실행 종료 직전 호출되어, 임시파일 스위프 및 대용량 컬렉션 참조 해제를 수행한다. |
| [`_worker`](../rom_list_core_cleaner.py) | 202–250 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`start_cleaner_thread`](../rom_list_core_cleaner.py) | 253–265 | 코드 참조 있음 | 정리기를 백그라운드 스레드로 기동한다. |
| [`run_once_blocking`](../rom_list_core_cleaner.py) | 268–272 | 코드 참조 있음 | 테스트/디버깅용: 동기 실행 |

## rom_list_popup.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`parse_cue_referenced_files`](../rom_list_popup.py) | 40–53 | 코드 참조 있음 | CUE의 FILE 항목을 읽어 실제 데이터 파일을 찾는다. CUE와 BIN을 각각 다른 게임으로 중복 표시하지 않기 위한 전처리다. |
| [`DraggableTextBrowser.__init__`](../rom_list_popup.py) | 57–59 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`DraggableTextBrowser.mousePressEvent`](../rom_list_popup.py) | 61–64 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`DraggableTextBrowser.mouseMoveEvent`](../rom_list_popup.py) | 66–71 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup.__init__`](../rom_list_popup.py) | 75–123 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup.build_top_section`](../rom_list_popup.py) | 125–210 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup.open_scraper_setting`](../rom_list_popup.py) | 212–214 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup.open_category_popup`](../rom_list_popup.py) | 216–238 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup.navigate_folder`](../rom_list_popup.py) | 240–248 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup._compute_cue_hidden_bins`](../rom_list_popup.py) | 250–266 | 코드 참조 있음 | cue가 참조하는 bin(또는 바이너리) 파일을 리스트에서 숨기기 위한 set |
| [`RomListPopup._collect_filtered_roms_and_subfolders`](../rom_list_popup.py) | 268–296 | 코드 참조 있음 | 현재 current_dir + 옵션(group_roms_by_folder) 기준으로 표시 대상 목록을 계산 |
| [`RomListPopup._make_display_name`](../rom_list_popup.py) | 298–311 | 코드 참조 있음 | 표시 모드(show_filename_mode / 폴더표시옵션 / 즐겨찾기) 반영한 문자열 |
| [`RomListPopup._rebuild_model_entries`](../rom_list_popup.py) | 313–351 | 코드 참조 있음 | 현재 상태 기준으로 엔트리 모델 재구성 |
| [`RomListPopup._calc_virtual_stride`](../rom_list_popup.py) | 353–356 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup._init_virtual_list_ui`](../rom_list_popup.py) | 358–407 | 코드 참조 있음 | 좌측 리스트를 스페이서+풀 구조로 구성 |
| [`RomListPopup._schedule_virtual_refresh`](../rom_list_popup.py) | 409–414 | 코드 참조 있음 | 같은 이벤트 처리 중 연속으로 들어온 갱신을 한 번의 예약 작업으로 합친다. |
| [`RomListPopup._refresh_virtual_view`](../rom_list_popup.py) | 416–460 | 코드 참조 있음 | 현재 스크롤 위치에 필요한 행만 재사용해 표시한다. |
| [`RomListPopup._apply_pool_selection_only`](../rom_list_popup.py) | 462–465 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup._ensure_index_visible`](../rom_list_popup.py) | 467–482 | 코드 참조 있음 | 모델 인덱스와 행 높이로 스크롤 위치를 계산한다. 위젯 풀의 행 번호와 전체 모델 인덱스를 혼동하지 않는다. |
| [`RomListPopup._get_entry`](../rom_list_popup.py) | 484–487 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup._find_entry_index_by_filename`](../rom_list_popup.py) | 489–497 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup._get_focused_rom_filename`](../rom_list_popup.py) | 499–503 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup.build_bottom_section`](../rom_list_popup.py) | 505–654 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup.apply_last_played_focus`](../rom_list_popup.py) | 656–701 | 코드 참조 있음 | 최근 실행 ROM을 찾아 초점을 복원한다. 정렬·폴더 이동으로 인덱스가 바뀔 수 있으므로 파일 식별자를 함께 사용한다. |
| [`RomListPopup.resizeEvent`](../rom_list_popup.py) | 703–712 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup.update_title_image_size`](../rom_list_popup.py) | 714–729 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup.update_screenshot_image`](../rom_list_popup.py) | 731–740 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup.set_focus_index`](../rom_list_popup.py) | 742–768 | 코드 참조 있음 | 목록 범위에 맞춰 선택을 바꾸고 우측 정보·스크롤·행 강조를 함께 갱신한다. |
| [`RomListPopup.keyPressEvent`](../rom_list_popup.py) | 770–823 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup.update_right_section`](../rom_list_popup.py) | 825–892 | 코드 참조 있음 | 선택 ROM의 텍스트와 이미지를 표시한다. 메타데이터가 없는 경우 빈 상태를 표시하는 것도 UI 갱신의 일부다. |
| [`RomListPopup.update_right_section.make_label`](../rom_list_popup.py) | 861–866 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup.sort_roms`](../rom_list_popup.py) | 894–903 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup.sort_roms.sort_key`](../rom_list_popup.py) | 896–901 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup.refresh_rom_list`](../rom_list_popup.py) | 905–1162 | 코드 참조 있음 | 사용자 확인 후 실제 폴더와 Classic JSON 목록을 비교한다. |
| [`RomListPopup.refresh_rom_list.insert_breakable_path`](../rom_list_popup.py) | 920–921 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup.open_search_popup`](../rom_list_popup.py) | 1164–1236 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup.open_search_popup.on_accepted`](../rom_list_popup.py) | 1206–1233 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup.launch_current_rom`](../rom_list_popup.py) | 1238–1355 | 코드 참조 있음 | ROM별 설정 → 기종 대표 설정 → 실행기 설정 순으로 빈 값을 보완한다. |
| [`RomListPopup.edit_rom_metadata`](../rom_list_popup.py) | 1357–1372 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup.toggle_favorite`](../rom_list_popup.py) | 1374–1401 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup.reopen_self`](../rom_list_popup.py) | 1403–1435 | 코드 참조 있음 | RomListPopup을 닫았다가 동일 인자로 다시 엽니다. |
| [`RomListPopup.reopen_self._reopen`](../rom_list_popup.py) | 1422–1433 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomListPopup.reload`](../rom_list_popup.py) | 1437–1462 | 코드 참조 있음 | rom_list.json을 다시 읽고 좌우 UI를 갱신합니다. |
| [`RomListPopup.closeEvent`](../rom_list_popup.py) | 1464–1478 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`RomItemWidget.__init__`](../rom_list_popup.py) | 1482–1520 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`RomItemWidget.bind_entry`](../rom_list_popup.py) | 1522–1538 | 코드 참조 있음 | (가상화) 재사용되는 위젯에 표시 내용/타입/인덱스를 다시 바인딩 |
| [`RomItemWidget.set_selected`](../rom_list_popup.py) | 1540–1550 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RomItemWidget.mousePressEvent`](../rom_list_popup.py) | 1552–1570 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`GameRunner.__init__`](../rom_list_popup.py) | 1582–1593 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`GameRunner.update_last_played`](../rom_list_popup.py) | 1595–1621 | 코드 참조 있음 | 카드 메타데이터와 개별 ROM의 최근 실행 시간을 각각 기록한다. 두 저장 위치의 목적이 다르다. |
| [`GameRunner.wait_all`](../rom_list_popup.py) | 1623–1686 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameRunner.wait_emulator`](../rom_list_popup.py) | 1688–1721 | 코드 참조 있음 | 실행기 프로세스의 시작과 종료를 확인한다. ROM 내부 종료가 아니라 에뮬레이터 프로세스를 감시한다. |
| [`GameRunner.wait_batch`](../rom_list_popup.py) | 1723–1734 | 코드 참조 있음 | 배치 프로세스 종료를 기다리고 에뮬레이터 감시와 완료 상태를 합친다. GUI 스레드에서 직접 호출하지 않는다. |
| [`GameRunner.check_restore`](../rom_list_popup.py) | 1736–1739 | 코드 참조 있음 | 에뮬레이터와 배치가 모두 끝났을 때 복귀를 요청한다. 최종 중복 방지는 restore_launcher의 잠금이 담당한다. |
| [`GameRunner.restore_launcher`](../rom_list_popup.py) | 1741–1747 | 코드 참조 있음 | 중복 복귀를 막고 한 번만 GUI 슬롯을 예약한다. |
| [`GameRunner._restore_launcher_ui`](../rom_list_popup.py) | 1750–1768 | 코드 참조 있음 | 목록 갱신과 전체화면 복귀를 GUI 스레드에서 수행한다. |

## scraper_credentials.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`load_flags`](../scraper_credentials.py) | 12–32 | 코드 참조 있음 | 기존 수집기 호출 규약을 유지하되 운영 데이터 파일은 읽지 않는다. |
| [`save_flags`](../scraper_credentials.py) | 35–44 | 코드 참조 있음 | 지역 등 환경설정만 저장한다. 사용자 ID·암호는 저장 대상에서 제외한다. |

## scraper_setting_popup.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`ScraperThread.__init__`](../scraper_setting_popup.py) | 37–41 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`ScraperThread.run`](../scraper_setting_popup.py) | 43–265 | Python/Qt 진입점 포함 | 선택 기종의 ROM 정보를 순차 수집하고 Classic JSON에 반영한다. |
| [`ScraperThread.run.sanitize_filename`](../scraper_setting_popup.py) | 54–55 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`ScraperThread.run.save_image`](../scraper_setting_popup.py) | 219–229 | 코드 참조 있음 | 응답 미디어를 ROM 이미지 폴더에 저장한다. 다운로드 실패는 해당 이미지의 실패로 처리한다. |
| [`ScraperThread.map_system_id`](../scraper_setting_popup.py) | 267–335 | 코드 참조 있음 | 런처 기종 식별자를 서비스의 시스템 번호로 바꾼다. 여러 번호를 지원하는 경우 순서대로 조회한다. |
| [`ScraperSettingPopup.__init__`](../scraper_setting_popup.py) | 339–373 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`ScraperSettingPopup.resize_popup`](../scraper_setting_popup.py) | 375–378 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`ScraperSettingPopup.setup_top_section`](../scraper_setting_popup.py) | 380–518 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`ScraperSettingPopup.load_scrap_config`](../scraper_setting_popup.py) | 520–539 | 코드 참조 있음 | 지역·작업 옵션을 복원하고 개인 인증 값은 환경변수에서 읽는다. 공개본은 계정 암호를 설정 JSON에 저장하지 않는다. |
| [`ScraperSettingPopup.save_scrap_config`](../scraper_setting_popup.py) | 541–561 | 코드 참조 있음 | 비밀정보를 제외한 수집 옵션만 저장한다. 실제 저장 경계는 scraper_credentials 모듈에서 다시 제한한다. |
| [`ScraperSettingPopup.setup_bottom_section`](../scraper_setting_popup.py) | 563–587 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`ScraperSettingPopup.on_scrap_clicked`](../scraper_setting_popup.py) | 589–617 | 코드 참조 있음 | 선택 기종과 옵션을 수집해 새 작업 스레드를 시작한다. 시그널 연결과 상태 초기화를 start보다 먼저 끝낸다. |
| [`ScraperSettingPopup.on_scrap_progress`](../scraper_setting_popup.py) | 619–621 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`ScraperSettingPopup._on_scrap_done_once`](../scraper_setting_popup.py) | 623–628 | 코드 참조 있음 | 완료 UI가 두 번 열리지 않도록 가드한다. 실패 알림과 스레드 종료 알림은 별개로 도착할 수 있다. |
| [`ScraperSettingPopup.on_scrap_done`](../scraper_setting_popup.py) | 630–650 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`ScraperSettingPopup.on_scrap_done.after_confirm`](../scraper_setting_popup.py) | 633–644 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`ScraperSettingPopup.on_scrap_failed`](../scraper_setting_popup.py) | 652–656 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`ScrapProgressPopup.__init__`](../scraper_setting_popup.py) | 660–704 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`ScrapProgressPopup.update_progress`](../scraper_setting_popup.py) | 706–710 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## sdl_automap.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`_extract_device_info`](../sdl_automap.py) | 17–64 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`_translate_tokens_to_profile`](../sdl_automap.py) | 67–159 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`_translate_tokens_to_profile._btn`](../sdl_automap.py) | 73–81 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`_translate_tokens_to_profile._axis`](../sdl_automap.py) | 83–97 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`_translate_tokens_to_profile._hat`](../sdl_automap.py) | 99–109 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`_flatten_to_legacy`](../sdl_automap.py) | 162–179 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`_flatten_from_sdl_auto_entry`](../sdl_automap.py) | 182–189 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`_load_profiles`](../sdl_automap.py) | 192–202 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`_save_profiles`](../sdl_automap.py) | 205–208 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`_merge_profile_legacy`](../sdl_automap.py) | 211–218 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`_migrate_existing_sdl_auto`](../sdl_automap.py) | 221–241 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`automap_for_devices`](../sdl_automap.py) | 244–280 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## sdl_gcdb.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`parse_gcdb_line`](../sdl_gcdb.py) | 20–42 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`load_gcdb`](../sdl_gcdb.py) | 45–54 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`_norm`](../sdl_gcdb.py) | 57–58 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`pick_best_with_reason`](../sdl_gcdb.py) | 61–87 | 코드 참조 있음 | 허용 우선순위: |

## service_settings.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`endpoint`](../service_settings.py) | 11–26 | 코드 참조 있음 | 설정된 HTTP 주소만 반환한다. 로컬 실습 외에는 HTTPS를 요구한다. |

## settings_popup.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`get_launcher_temp_dir`](../settings_popup.py) | 35–45 | 코드 참조 있음 | 런쳐 실행 폴더 기준으로 전용 임시폴더(launcher_temp)를 만들어 경로를 반환합니다. |
| [`is_internet_available`](../settings_popup.py) | 48–53 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`DraggableScrollArea.__init__`](../settings_popup.py) | 57–61 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`DraggableScrollArea.mousePressEvent`](../settings_popup.py) | 63–66 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`DraggableScrollArea.mouseMoveEvent`](../settings_popup.py) | 68–75 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`DraggableScrollArea.mouseReleaseEvent`](../settings_popup.py) | 77–79 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`SettingsPopup.init_ui`](../settings_popup.py) | 83–191 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`SettingsPopup.delete_category_confirmed`](../settings_popup.py) | 193–199 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`SettingsPopup._get_font`](../settings_popup.py) | 201–206 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`SettingsPopup.get_font_and_color`](../settings_popup.py) | 208–214 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`SettingsPopup.build_category_tab`](../settings_popup.py) | 216–243 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`SettingsPopup.load_categories`](../settings_popup.py) | 245–257 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`SettingsPopup.move_category`](../settings_popup.py) | 259–272 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`SettingsPopup.save_categories`](../settings_popup.py) | 274–276 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`SettingsPopup.add_category`](../settings_popup.py) | 278–298 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`SettingsPopup.add_category_item`](../settings_popup.py) | 300–348 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`SettingsPopup.edit_category`](../settings_popup.py) | 350–376 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`SettingsPopup.finish_edit_category`](../settings_popup.py) | 378–424 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`SettingsPopup.delete_category`](../settings_popup.py) | 426–433 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`SettingsPopup.keyPressEvent`](../settings_popup.py) | 435–444 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`SettingsPopup.open_game_popup`](../settings_popup.py) | 446–475 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`SettingsPopup.switch_tab`](../settings_popup.py) | 477–490 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`SettingsPopup.closeEvent`](../settings_popup.py) | 492–509 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |

## steam_crawler.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`_extract_screenshot_urls_from_html`](../steam_crawler.py) | 16–97 | 코드 참조 있음 | Steam 상점 HTML에서 스크린샷 URL을 최대한 robust 하게 추출합니다. |
| [`_extract_screenshot_urls_from_html.add`](../steam_crawler.py) | 27–46 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`register_game`](../steam_crawler.py) | 100–201 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## steam_scanner.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`get_steam_root_from_registry`](../steam_scanner.py) | 12–19 | 코드 참조 있음 | 현재 Windows 사용자의 Steam 설치 경로를 레지스트리에서 읽는다. 조회 실패 시 None을 반환한다. |
| [`get_library_folders`](../steam_scanner.py) | 22–34 | 코드 참조 있음 | libraryfolders.vdf에서 복수 라이브러리 경로를 추출한다. 단순 정규식 파싱이므로 VDF 전체 문법 구현은 아니다. |
| [`get_appinfo_path`](../steam_scanner.py) | 37–39 | 코드 참조 있음 | Steam 설치 루트에서 appcache/appinfo.vdf 위치를 계산한다. |
| [`get_exe_name_by_vdfparse`](../steam_scanner.py) | 42–63 | 코드 참조 있음 | 외부 VDFparse를 통해 바이너리 appinfo에서 실행 파일 정보를 얻는다. 도구 또는 데이터가 없으면 빈 문자열이다. |
| [`scan_installed_steam_games`](../steam_scanner.py) | 66–134 | 코드 참조 있음 | 라이브러리별 appmanifest를 읽고 설치 경로·상품 ID·실행 파일 후보를 모은다. 상점 스크래핑과 설치 검색을 분리한다. |

## stove_scanner.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`load_slug_map`](../stove_scanner.py) | 10–22 | 코드 참조 있음 | 자체 설정한 매핑 주소만 조회한다. 공개본에는 제작자의 운영 서버 주소나 기본 매핑 데이터가 없다. |
| [`find_slug`](../stove_scanner.py) | 25–37 | 코드 참조 있음 | 로컬 게임 제목을 매핑 데이터의 상품 번호와 연결한다. 제목 규칙이 달라지면 매핑을 갱신해야 한다. |
| [`scan_stove_games`](../stove_scanner.py) | 40–106 | 코드 참조 있음 | 클라이언트 설정과 매니페스트에서 설치 게임을 읽는다. 실제 상품 수집은 등록 작업 단계에서 수행한다. |

## system_config_handler.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`get_default_audio_volume`](../system_config_handler.py) | 28–33 | 코드 참조 있음 | 기본 재생 장치의 볼륨을 0~1 실수로 읽는다. 장치 오류는 호출자에게 전달한다. |
| [`set_audio_volume`](../system_config_handler.py) | 36–43 | 코드 참조 있음 | 기본 장치 볼륨을 설정한다. 잘못된 값으로 기존 볼륨을 덮어쓰지 않는다. |
| [`parse_resolution`](../system_config_handler.py) | 46–54 | 코드 참조 있음 | '1920x1080'을 양의 정수 쌍으로 변환한다. 잘못된 입력은 (None, None). |
| [`apply_resolution`](../system_config_handler.py) | 57–79 | 코드 참조 있음 | 외부 도구의 성공 종료를 확인한다. 도구가 멈춰도 15초 이상 기다리지 않는다. |
| [`get_current_resolution`](../system_config_handler.py) | 82–89 | 코드 참조 있음 | 실제 모니터 상태를 읽는다. 실패 시 임의의 해상도를 복구값으로 만들지 않는다. |
| [`_save_snapshot`](../system_config_handler.py) | 92–109 | 코드 참조 있음 | 변경 전에 복구 기록을 완성한다. 쓰기 실패 시 장치 설정은 건드리지 않는다. |
| [`apply_preset`](../system_config_handler.py) | 112–163 | 코드 참조 있음 | 프리셋 적용 성공 또는 미설정이면 True, 적용 실패이면 False. |
| [`restore_system_settings`](../system_config_handler.py) | 166–193 | 코드 참조 있음 | 남아 있는 복구 기록을 처리한다. 모두 복구했거나 기록이 없으면 True. |

## system_info_util.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`get_system_volume_percent`](../system_info_util.py) | 9–26 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`get_monitor_info`](../system_info_util.py) | 29–113 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`get_available_display_modes`](../system_info_util.py) | 116–169 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`get_system_log_string`](../system_info_util.py) | 172–193 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## tab_info.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`build_info_tab`](../tab_info.py) | 6–15 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## tab_launcher.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`get_launcher_temp_dir`](../tab_launcher.py) | 32–42 | 코드 참조 있음 | 런쳐 실행 폴더 기준으로 전용 임시폴더(launcher_temp)를 만들어 경로를 반환합니다. |
| [`set_startup_enabled`](../tab_launcher.py) | 45–61 | 코드 참조 있음 | Windows 시작프로그램 폴더에 바로가기를 생성하거나 제거한다. 실행 파일 자체를 복사하는 동작은 아니다. |
| [`build_launcher_tab`](../tab_launcher.py) | 64–590 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`build_launcher_tab.apply_border_theme`](../tab_launcher.py) | 85–94 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`build_launcher_tab.apply_popup_label_style`](../tab_launcher.py) | 96–105 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`build_launcher_tab.setting_row`](../tab_launcher.py) | 107–116 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`build_launcher_tab.build_toggle_button`](../tab_launcher.py) | 118–140 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`build_launcher_tab.save_config_value`](../tab_launcher.py) | 175–187 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`build_launcher_tab.apply_theme_and_restart`](../tab_launcher.py) | 189–242 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`build_launcher_tab.on_hhc_toggled`](../tab_launcher.py) | 254–271 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`build_launcher_tab.on_hhc_toggled._find_main_widget`](../tab_launcher.py) | 257–263 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`build_launcher_tab.open_remap_flow`](../tab_launcher.py) | 280–447 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`build_launcher_tab.open_remap_flow._ok`](../tab_launcher.py) | 355–358 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`build_launcher_tab.open_remap_flow._cancel`](../tab_launcher.py) | 360–361 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`build_launcher_tab.open_remap_flow._find_main_widget`](../tab_launcher.py) | 383–389 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`build_launcher_tab.reset_library`](../tab_launcher.py) | 452–459 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`build_launcher_tab.perform_library_reset`](../tab_launcher.py) | 461–472 | 코드 참조 있음 | 런처의 l_libs 등록 데이터를 삭제한다. 일반 게임 설치 경로가 아니라 이 상대 경로만 대상이며 확인은 호출부에서 받는다. |
| [`build_launcher_tab.restart_launcher`](../tab_launcher.py) | 474–496 | 코드 참조 있음 | 현재 프로세스가 종료된 뒤 재실행하도록 임시 배치를 만든다. 자신이 살아 있는 동안 같은 실행 파일을 교체하려는 용도가 아니다. |
| [`build_launcher_tab.on_label_clicked`](../tab_launcher.py) | 565–576 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`build_launcher_tab.cleanup`](../tab_launcher.py) | 585–587 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## tab_profile.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`build_profile_tab`](../tab_profile.py) | 6–16 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |

## tests/test_public_source.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`example`](../tests/test_public_source.py) | 20–26 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`PublicSourceTests.test_empty_keys_and_password_not_saved`](../tests/test_public_source.py) | 30–42 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`PublicSourceTests.test_environment_key_and_no_legacy_decryption`](../tests/test_public_source.py) | 44–58 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`PublicSourceTests.test_bootstrap_preserves_user_settings`](../tests/test_public_source.py) | 60–66 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`PublicSourceTests.test_unconfigured_slug_does_not_connect`](../tests/test_public_source.py) | 68–76 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`PublicSourceTests.test_local_login_and_notice_queue`](../tests/test_public_source.py) | 78–122 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`PublicSourceTests.test_release_hash_and_oauth_state`](../tests/test_public_source.py) | 124–142 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |

## tests/test_review_regressions.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`CdpTests.test_event_before_reply_and_socket_closed`](../tests/test_review_regressions.py) | 15–25 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`CdpTests.test_broken_reply_closes_socket`](../tests/test_review_regressions.py) | 27–34 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`CdpTests.test_unsolicited_events_have_total_deadline`](../tests/test_review_regressions.py) | 36–47 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`PresetTests.setUp`](../tests/test_review_regressions.py) | 52–61 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`PresetTests.write_preset`](../tests/test_review_regressions.py) | 63–64 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`PresetTests.test_failed_resolution_keeps_journal_but_restores_volume`](../tests/test_review_regressions.py) | 66–78 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`PresetTests.test_unreadable_display_cannot_create_fake_snapshot`](../tests/test_review_regressions.py) | 80–91 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`PresetTests.test_volume_failure_rolls_back_resolution`](../tests/test_review_regressions.py) | 93–116 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`PresetTests.test_invalid_preset_fails_before_change`](../tests/test_review_regressions.py) | 118–126 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`UiBoundaryTests.test_duplicate_initialization_removed`](../tests/test_review_regressions.py) | 131–167 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`UiBoundaryTests.test_concurrent_emulator_completion_returns_on_gui_once`](../tests/test_review_regressions.py) | 169–197 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`RegistrationTests.test_failure_isolated_and_empty_output_list_shared`](../tests/test_review_regressions.py) | 201–223 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`RegistrationTests.test_failure_isolated_and_empty_output_list_shared.crawler`](../tests/test_review_regressions.py) | 207–211 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`RegistrationTests.test_auth_marker_from_previous_attempt_is_not_reused`](../tests/test_review_regressions.py) | 225–236 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`RegistrationTests.test_registration_waits_for_finished_before_auth_retry`](../tests/test_review_regressions.py) | 238–258 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`ResourceTests.test_gog_missing_database_is_not_created`](../tests/test_review_regressions.py) | 263–269 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`ResourceTests.test_bad_core_archive_keeps_existing_dll_and_cleans_temp`](../tests/test_review_regressions.py) | 271–303 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`ResourceTests.test_notice_queue_advances_only_on_actual_close`](../tests/test_review_regressions.py) | 305–331 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`ResourceTests.test_notice_queue_advances_only_on_actual_close.FakePopup.__init__`](../tests/test_review_regressions.py) | 315–316 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`FormTests.test_extra_input_does_not_shift_metadata_fields`](../tests/test_review_regressions.py) | 336–370 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |

## tests/test_teaching_examples.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`TeachingExamplesTests.test_http_pagination_and_logout`](../tests/test_teaching_examples.py) | 12–42 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`TeachingExamplesTests.test_notice_paging_backup_and_validation`](../tests/test_teaching_examples.py) | 44–62 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`TeachingExamplesTests.test_durable_queue_restart_ack_and_duplicate`](../tests/test_teaching_examples.py) | 64–78 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |
| [`TeachingExamplesTests.test_theme_strings_are_not_paths`](../tests/test_teaching_examples.py) | 80–87 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |

## tests/test_ui_smoke.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`UiSmokeTests.test_empty_library_and_unlocked_settings`](../tests/test_ui_smoke.py) | 16–69 | 정적 참조 없음: 별도 실행/외부 호출 확인 대상 | 구현 및 상위 호출 흐름 참고 |

## theme_manager.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`ThemeManager.__init__`](../theme_manager.py) | 9–16 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`ThemeManager.load_theme`](../theme_manager.py) | 18–28 | 코드 참조 있음 | theme.json을 로드하여 딕셔너리로 저장 |
| [`ThemeManager.get`](../theme_manager.py) | 30–70 | 코드 참조 있음 | 'fonts.팝업라벨.size'처럼 점으로 구분한 키를 중첩 사전에서 찾는다. |
| [`ThemeManager.scale_px`](../theme_manager.py) | 72–75 | 코드 참조 있음 | DPI와 해상도 기반 스케일을 함께 고려하여 픽셀 수를 보정합니다. |

## top_bar.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`TopBar.__init__`](../top_bar.py) | 17–24 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`TopBar.update_button_styles`](../top_bar.py) | 26–34 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`TopBar.keyPressEvent`](../top_bar.py) | 36–50 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`TopBar.eventFilter`](../top_bar.py) | 52–67 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`TopBar.setup_ui`](../top_bar.py) | 69–143 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`TopBar._get_font_from_theme`](../top_bar.py) | 145–150 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`TopBar.set_profile_icon`](../top_bar.py) | 152–181 | 코드 참조 있음 | 로컬 프로필 이미지가 있으면 사용하고 없으면 테마 기본 이미지를 사용한다. 공개본에서는 계정 서버에 요청하지 않는다. |
| [`TopBar.open_settings`](../top_bar.py) | 183–184 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`TopBar.update_time`](../top_bar.py) | 186–188 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`TopBar.update_battery_status`](../top_bar.py) | 190–223 | 코드 참조 있음 | 배터리 정보를 아이콘·백분율로 표시한다. 배터리 없는 데스크톱도 처리한다. |
| [`TopBar.get_wifi_signal_strength`](../top_bar.py) | 225–244 | 코드 참조 있음 | netsh의 지역화된 출력에서 신호 세기를 읽는다. 운영체제 언어·출력 형식 의존성을 가진 부분이다. |
| [`TopBar.get_wifi_icon_from_signal`](../top_bar.py) | 246–256 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`TopBar.update_network_status`](../top_bar.py) | 258–297 | 코드 참조 있음 | 인터페이스 이름과 활성 상태로 유선·무선 아이콘을 고른다. 링크 활성은 인터넷이나 로그인 서버 접속 성공을 의미하지 않는다. |

## update_popup.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`UpdatePopup.__init__`](../update_popup.py) | 10–22 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |

## user_register_popup.py

| 함수 | 줄 | 참조 구분 | 역할/읽기 단서 |
|---|---:|---|---|
| [`SteamScrapeWorker.__init__`](../user_register_popup.py) | 35–37 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`SteamScrapeWorker.run`](../user_register_popup.py) | 39–43 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`SteamSearchWorker.__init__`](../user_register_popup.py) | 49–51 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`SteamSearchWorker.run`](../user_register_popup.py) | 53–55 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`GameRegisterEditPopup.__init__`](../user_register_popup.py) | 59–87 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`GameRegisterEditPopup.init_ui`](../user_register_popup.py) | 89–289 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameRegisterEditPopup.init_thumbnail_section`](../user_register_popup.py) | 291–298 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameRegisterEditPopup.init_header_section`](../user_register_popup.py) | 300–307 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameRegisterEditPopup.init_metadata_section`](../user_register_popup.py) | 309–396 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameRegisterEditPopup.init_metadata_section.row`](../user_register_popup.py) | 322–335 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameRegisterEditPopup.on_register_clicked`](../user_register_popup.py) | 398–528 | 코드 참조 있음 | 입력값과 선택 이미지를 로컬 라이브러리에 저장한다. |
| [`GameRegisterEditPopup.fill_existing_data`](../user_register_popup.py) | 530–566 | 코드 참조 있음 | 편집할 게임의 기존 텍스트·이미지 경로를 폼에 복원한다. 메타데이터 사전의 누락 필드는 기본값으로 처리한다. |
| [`GameRegisterEditPopup.select_thumbnail_image`](../user_register_popup.py) | 568–577 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameRegisterEditPopup.select_header_image`](../user_register_popup.py) | 579–588 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameRegisterEditPopup.select_exe_file`](../user_register_popup.py) | 590–595 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameRegisterEditPopup.open_search_popup`](../user_register_popup.py) | 597–767 | 코드 참조 있음 | 검색어로 후보를 조회하고 선택한 게임의 정보를 폼에 채운다. 입력 폼의 등록 버튼을 누르기 전에는 등록을 확정하지 않는다. |
| [`GameRegisterEditPopup.open_search_popup.SearchPopup.__init__`](../user_register_popup.py) | 611–681 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`GameRegisterEditPopup.open_search_popup.SearchPopup.__init__.show_alert_and_close`](../user_register_popup.py) | 642–649 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameRegisterEditPopup.open_search_popup.SearchPopup.item_selected`](../user_register_popup.py) | 683–699 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameRegisterEditPopup.open_search_popup.SearchPopup.on_scrape_finished`](../user_register_popup.py) | 701–737 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameRegisterEditPopup.open_search_popup.launch_popup`](../user_register_popup.py) | 759–763 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameRegisterEditPopup.select_screenshots`](../user_register_popup.py) | 769–793 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameRegisterEditPopup.confirm_remove_screenshot`](../user_register_popup.py) | 795–820 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameRegisterEditPopup.bind_screenshot_click`](../user_register_popup.py) | 822–828 | 코드 참조 있음 | 클로저에 현재 이미지 인덱스를 보관한다. 반복문의 마지막 인덱스가 모든 콜백에 공유되는 문제를 피한다. |
| [`GameRegisterEditPopup.bind_screenshot_click.on_click`](../user_register_popup.py) | 825–826 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameRegisterEditPopup.render_screenshots`](../user_register_popup.py) | 830–845 | 코드 참조 있음 | 선택한 스크린샷 목록으로 미리보기를 다시 만든다. 클릭 콜백에는 각 이미지의 인덱스를 고정해 연결한다. |
| [`GameRegisterEditPopup.closeEvent`](../user_register_popup.py) | 847–848 | Python/Qt 진입점 포함 | 구현 및 상위 호출 흐름 참고 |
| [`GameRegisterEditPopup.reject`](../user_register_popup.py) | 850–855 | 코드 참조 있음 | 구현 및 상위 호출 흐름 참고 |
| [`GameRegisterEditPopup.cleanup`](../user_register_popup.py) | 857–860 | 코드 참조 있음 | 창의 자식 위젯을 이벤트 처리 후 해제한다. 파일 삭제나 게임 제거를 수행하는 함수가 아니다. |
