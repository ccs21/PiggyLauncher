# 코드 지도

대표 진입점에서 호출을 따라 읽는다. 콜백·이벤트 핸들러는 직접 호출이 보이지 않아도 Qt나 입력 처리에서 사용될 수 있다.

## 화면과 설정

| 파일 | 먼저 읽을 함수·클래스 |
|---|---|
| [main.py](../main.py) | `check_chrome_installed`, `get_current_monitor_id`, `get_monitor_scale`, `get_monitor_resolution`, `SplashWindow` |
| [theme_manager.py](../theme_manager.py) | `ThemeManager` |
| [top_bar.py](../top_bar.py) | `TopBar` |
| [bottom_bar.py](../bottom_bar.py) | `BottomBar` |
| [central_content.py](../central_content.py) | `CentralContent` |
| [settings_popup.py](../settings_popup.py) | `get_launcher_temp_dir`, `is_internet_available`, `DraggableScrollArea`, `SettingsPopup` |
| [tab_launcher.py](../tab_launcher.py) | `get_launcher_temp_dir`, `set_startup_enabled`, `build_launcher_tab` |
| [tab_profile.py](../tab_profile.py) | `build_profile_tab` |
| [tab_info.py](../tab_info.py) | `build_info_tab` |
| [popup_windows.py](../popup_windows.py) | `BasePopup` |
| [popup_alert.py](../popup_alert.py) | `CustomAlertDialog` |
| [popup_utils.py](../popup_utils.py) | `ConfirmDialog`, `ProgressDialog` |
| [popup_loading_launcher.py](../popup_loading_launcher.py) | `launch_popup_with_loading` |
| [category_select_popup.py](../category_select_popup.py) | `DraggableScrollArea`, `CategorySelectPopup` |

실습과 구현 배경은 [학습 안내](LEARNING_GUIDE.md)를 함께 읽는다.

## PC 게임 등록

| 파일 | 먼저 읽을 함수·클래스 |
|---|---|
| [auto_register_popup.py](../auto_register_popup.py) | `debug_top_windows`, `SmartLabel`, `DraggableScrollArea`, `AutoRegisterPopup` |
| [user_register_popup.py](../user_register_popup.py) | `SteamScrapeWorker`, `SteamSearchWorker`, `GameRegisterEditPopup` |
| [register_thread.py](../register_thread.py) | `RegisterThread` |
| [register_progress_popup.py](../register_progress_popup.py) | `RegisterProgressPopup` |
| [steam_scanner.py](../steam_scanner.py) | `get_steam_root_from_registry`, `get_library_folders`, `get_appinfo_path`, `get_exe_name_by_vdfparse` |
| [epic_scanner.py](../epic_scanner.py) | `normalize_title`, `load_slug_map`, `find_slug`, `scan_epic_games` |
| [gog_scanner.py](../gog_scanner.py) | `get_db_path`, `scan_gog_installed_games`, `main` |
| [stove_scanner.py](../stove_scanner.py) | `load_slug_map`, `find_slug`, `scan_stove_games` |
| [steam_crawler.py](../steam_crawler.py) | `_extract_screenshot_urls_from_html`, `register_game` |
| [gog_crawler.py](../gog_crawler.py) | `get_slug_from_local_db`, `register_game` |
| [cdp_browser_controller.py](../cdp_browser_controller.py) | `get_chrome_path`, `launch_browser`, `kill_all_cdp_chrome`, `kill_all_chrome` |
| [cdp_register_common.py](../cdp_register_common.py) | `get_all_tabs`, `find_tab`, `is_valid_ws_url`, `evaluate` |
| [cdp_scraper.py](../cdp_scraper.py) | `generate_login_notice_html`, `send_command`, `scrape_steam_search_results`, `scrape_steam_metadata` |
| [cdp_dom_scraper_steam.py](../cdp_dom_scraper_steam.py) | `generate_html_file`, `wait_for_game_tab`, `scrape_and_register`, `run_single_steam_cdp_register` |
| [cdp_dom_scraper_epic.py](../cdp_dom_scraper_epic.py) | `run_cdp_register_epic` |
| [cdp_dom_scraper_stove.py](../cdp_dom_scraper_stove.py) | `run_cdp_register_stove` |

실습과 구현 배경은 [학습 안내](LEARNING_GUIDE.md)를 함께 읽는다.

## 실행과 복귀

| 파일 | 먼저 읽을 함수·클래스 |
|---|---|
| [game_detail_screen.py](../game_detail_screen.py) | `DraggableScrollArea`, `GameDetailScreen` |
| [emulator_launcher.py](../emulator_launcher.py) | `get_launcher_temp_dir`, `launch_game`, `launch_bat_after_delay` |
| [batch_setting_popup.py](../batch_setting_popup.py) | `BatchSettingPopup` |
| [graphic_setting_popup.py](../graphic_setting_popup.py) | `GraphicSettingPopup`, `get_current_monitor_id` |
| [system_config_handler.py](../system_config_handler.py) | `get_default_audio_volume`, `set_audio_volume`, `parse_resolution`, `apply_resolution`, `get_current_resolution` |
| [system_info_util.py](../system_info_util.py) | `get_system_volume_percent`, `get_monitor_info`, `get_available_display_modes`, `get_system_log_string` |

실습과 구현 배경은 [학습 안내](LEARNING_GUIDE.md)를 함께 읽는다.

## ROM 관리

| 파일 | 먼저 읽을 함수·클래스 |
|---|---|
| [emulator_register_popup.py](../emulator_register_popup.py) | `DraggableScrollArea`, `EmulatorRegisterPopup` |
| [core_edit_popup.py](../core_edit_popup.py) | `RomEditPopup` |
| [core_installer.py](../core_installer.py) | `CoreDownloadWorker`, `RetroArchInfo`, `CoreInstaller` |
| [rom_list_popup.py](../rom_list_popup.py) | `parse_cue_referenced_files`, `DraggableTextBrowser`, `RomListPopup`, `RomItemWidget`, `GameRunner` |
| [rom_edit_popup.py](../rom_edit_popup.py) | `RomEditPopup` |
| [rom_list_core_cleaner.py](../rom_list_core_cleaner.py) | `_log`, `_normalize_path`, `_safe_load_json`, `_atomic_write_json`, `_collect_all_string_values` |
| [ra_map_full.py](../ra_map_full.py) |  |
| [scraper_setting_popup.py](../scraper_setting_popup.py) | `ScraperThread`, `ScraperSettingPopup`, `ScrapProgressPopup` |
| [scraper_credentials.py](../scraper_credentials.py) | `load_flags`, `save_flags` |

실습과 구현 배경은 [학습 안내](LEARNING_GUIDE.md)를 함께 읽는다.

## 입력과 알림

| 파일 | 먼저 읽을 함수·클래스 |
|---|---|
| [gamepad_handler.py](../gamepad_handler.py) | `GamepadHandler` |
| [gamepad_manager.py](../gamepad_manager.py) | `load_profiles`, `get_unmapped_gamepads` |
| [gamepad_config_popup.py](../gamepad_config_popup.py) | `GamepadConfigPopup` |
| [button_mapping_popup.py](../button_mapping_popup.py) | `ButtonMappingPopup` |
| [sdl_automap.py](../sdl_automap.py) | `_extract_device_info`, `_translate_tokens_to_profile`, `_flatten_to_legacy`, `_flatten_from_sdl_auto_entry`, `_load_profiles` |
| [sdl_gcdb.py](../sdl_gcdb.py) | `GcdbEntry`, `parse_gcdb_line`, `load_gcdb`, `_norm`, `pick_best_with_reason` |
| [our_gamepad_db.py](../our_gamepad_db.py) | `_load_file`, `load`, `lookup` |
| [notification_manager.py](../notification_manager.py) | `load_noti_history`, `save_noti_history`, `NotificationManager` |
| [notification_popup.py](../notification_popup.py) | `NotificationPopup` |

실습과 구현 배경은 [학습 안내](LEARNING_GUIDE.md)를 함께 읽는다.

## 공개본 경계

| 파일 | 먼저 읽을 함수·클래스 |
|---|---|
| [bootstrap.py](../bootstrap.py) | `prepare_workspace` |
| [service_settings.py](../service_settings.py) | `endpoint` |
| [update_popup.py](../update_popup.py) | `UpdatePopup` |

실습과 구현 배경은 [학습 안내](LEARNING_GUIDE.md)를 함께 읽는다.
