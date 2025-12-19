#!/usr/bin/env python3
import sys
import traceback
from types import TracebackType


def except_hook(t, e: BaseException, tr: TracebackType):
    if isinstance(e, Exception):
        traceback.print_exception(t, e, tr)
        input("Press Enter to Exit")


sys.excepthook = except_hook

import os


import fa_paths
import multiplayer
from fa_menu import *
import modify_config
import launch_and_monitor
import save_management
from fa_arg_parse import args
from map_gen_setting_menu import map_menu
from translations import check_lang
from fa_scenarios import get_scenarios, pre_launch_scenario
from fa_mod_menu import mod_menu, check_for_main_mod
from version import version
from credentials_menu import sign_in_menu
from github_mods import update_all
from launcher_update import check_and_update



def main():
    menu = {
        "Launch last played": launch_and_monitor.just_launch,
        ("gui-menu.single-player-menu",): {
            ("gui-menu.new-game",): {
                ("gui-new-game.main-game",): map_menu,
                ("gui-new-game.mod-scenarios",): pre_launch_scenario,
            },
            ("gui-menu.load-game",): {
                save_management.get_menu_saved_games: launch_and_monitor.launch,
            },
        },
        ("gui-menu.multi-player-menu",): {
            multiplayer.get_username_menu: sign_in_menu,
            "Host Settings": multiplayer.host_settings_menu(),
            ("gui-menu.host-saved-game",): {
                save_management.get_menu_saved_games: multiplayer.multiplayer_host,
            },
            ("gui-menu.browse-public-games",): {
                "Friend List": multiplayer.friend_list,
                "List Games With Friends": {
                    multiplayer.games_with_friends_menu: multiplayer.multiplayer_join
                },
            },
            ("gui-menu.connect-to-address",): launch_and_monitor.connect_to_address_menu,
        },
        ("gui-menu.mods",): mod_menu,
        ("gui-menu.about",): {
            "Factorio": {
                "_desc": fa_paths.FACTORIO_VERSION,
            },
            "Launcher": {
                "_desc": f"Factorio Access Launcher Version {version.tag}\nCommit:{version.commit}"
            },
        },
        ("gui.exit",): launch_and_monitor.time_to_exit,
    }

    update_all()

    check_lang()
    check_for_main_mod()
    modify_config.do_config_check()

    if args.launch:
        launch_and_monitor.launch_with_params([], save_rename=False)
    else:

        main_menu = new_menu(("gui-menu.main-menu",), menu)
        main_menu()


# Check for launcher updates first - if applied, skip main and exit cleanly
if not check_and_update():
    main()
