#!/usr/bin/env python3
import sys
import traceback
sys.excepthook = lambda *args: (traceback.print_exception(*args), input("Press Enter to Exit"))

import os
import json
import shutil


import fa_paths
import multiplayer
from fa_menu import *
import modify_config
import launch_and_monitor
import save_management
from fa_arg_parse import args
from map_gen_setting_menu import sub_preset

os.chdir(fa_paths.MY_CONFIG_DIR)


    
menu = {
    "Launch last played":launch_and_monitor.just_launch,
    ("gui-menu.single-player-menu",):{
        ("gui-menu.new-game",): sub_preset,
        ("gui-menu.load-game",) : {
            save_management.get_menu_saved_games:launch_and_monitor.launch,
            },
        },
    ("gui-menu.multi-player-menu",):{
        multiplayer.get_username_menu:multiplayer.username_menu,
        "Host Settings":{
            multiplayer.get_host_settings_menu:multiplayer.run_func
        },
        ("gui-menu.host-saved-game",): {
            save_management.get_menu_saved_games: multiplayer.multiplayer_host,
            },
        ("gui-menu.browse-public-games",):{
            "Friend List":{
                "Add":multiplayer.add_friend_menu,
                 multiplayer.get_friends_menu: multiplayer.specific_friend_menu
            },
            "List Games With Friends":{
                multiplayer.games_with_friends_menu: multiplayer.multiplayer_join
            }
        },
        ("gui-menu.connect-to-address",): launch_and_monitor.connect_to_address_menu,
        },
    ("gui.exit",): launch_and_monitor.time_to_exit,
    }

modify_config.do_config_check()

if args.launch:
    launch_and_monitor.launch_with_params([])
else:
    my_main_menu = menu_item(("gui-menu.main-menu",),menu,None,False)
    my_main_menu()
    #do_menu(menu,"Main Menu",False)