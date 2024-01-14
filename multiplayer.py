import os
import json
from typing import Final
import re

import config
import update_factorio
import fa_paths
from fa_menu import do_menu
import launch_and_monitor

__ACCESS_LIST_PATH : Final[str] = os.path.join(fa_paths.WRITE_DIR,"server-whitelist.json")

def get_game_list():
    cred = update_factorio.get_credentials()
    url=f"https://multiplayer.factorio.com/get-games?username={cred['username']}&token={cred['token']}"
    with update_factorio.opener.open(url) as fp:
        games = json.load(fp)
    with open("all_games",'w') as fp:
        json.dump(games,fp, indent=2)
    return games

def get_game(game_id):
    url=f"https://multiplayer.factorio.com/get-game-details/{game_id}"
    with update_factorio.opener.open(url) as fp:
        game = json.load(fp)
    with open(f"game_{game_id}",'w') as fp:
        json.dump(game,fp, indent=2)
    return game

def get_filtered_game_list():
    games = get_game_list()
    friends = set(get_friend_list())
    return [game for game in games if set(game.get("players",[])) & friends]

def get_friend_list():
    try:
        with open(__ACCESS_LIST_PATH) as fp:
            return json.load(fp)
    except:
        return []

def add_friend(friend:str):
    with open(__ACCESS_LIST_PATH, 'a+', newline="") as fp:
        fp.seek(0)
        try:
            friends:list[str] = json.load(fp)
        except:
            friends=[]
        friends.append(friend)
        fp.seek(0)
        fp.truncate()
        json.dump(friends,fp, indent=2)

def remove_friend(friend:str):
    with open(__ACCESS_LIST_PATH, 'r+', newline="") as fp:
        friends = set(json.load(fp))
        friends.remove(friend)
        fp.seek(0)
        fp.truncate()
        json.dump(list(friends),fp, indent=2)
    return 0
def multiplayer_join(game_id):
    game=get_game(game_id)
    if fa_paths.BIN.count('steam') and 'steam_id' in game:
        launch_and_monitor.launch_with_params(['--join-game-by-steam-id',game['steam_id']])
    else:
        launch_and_monitor.connect_to_address(game['host_address'])

def multiplayer_host(game):
    with config.current_conf:
        if config.multiplayer_lobby.name == "":
            config.multiplayer_lobby.name="FactorioAccessDefault"
        player = update_factorio.get_player_data()
        player["last-played"] = {
            "type": "hosted-multiplayer",
            "host-settings": 
            {
            "server-game-data": 
            {
                "visibility": {
                    "public": config.multiplayer_lobby.visibility_public,
                    "steam": config.multiplayer_lobby.visibility_steam,
                    "lan": config.multiplayer_lobby.visibility_lan
                },
                "name": config.multiplayer_lobby.name,
                "description": config.multiplayer_lobby.description,
                "max_players": config.multiplayer_lobby.max_players,
                "game_time_elapsed": 150,
                "has_password": config.multiplayer_lobby.password!=""
            },
            "server-username": player["service-username"],
            "autosave-interval": config.other.autosave_interval,
            "afk-autokick-interval": config.multiplayer_lobby.afk_auto_kick
            },
            "save-name": game[:-4]
        }
    update_factorio.set_player_data(player)
    return launch_and_monitor.launch_with_params([],announce_press_e=True,tweak_modified=os.path.join(fa_paths.SAVES,game))

def add_toggle_setting(menu,setting,header):
    name = header+": "
    t_setting=("multiplayer-lobby",setting)
    current=config.current_conf.get_setting(*t_setting)
    if current == "true":
        name += "Yes"
        def toggle():
            with config.current_conf:
                config.current_conf.set_setting(*t_setting,'false')
            return 0
    else:
        name += "No"
        def toggle():
            with config.current_conf:
                config.current_conf.set_setting(*t_setting,'true')
            return 0
    menu[name]=toggle

def get_host_settings_menu():
    with config.current_conf:
        menu={}
        add_toggle_setting(menu,"visibility-public","Publicly Advertised")
        add_toggle_setting(menu,"visibility-lan","LAN Advertised")
        add_toggle_setting(menu,"visibility-steam","Steam Advertised")
        add_toggle_setting(menu,"enable-whitelist","Friends Only")
        add_toggle_setting(menu,"verify-user-identity","Verify user")
        return menu
def run_func(func):
    return func()

def get_username_menu():
    try:
        player=update_factorio.get_player_data()
        return "Username: "+player["service-username"]
    except:
        return False

def get_friends_menu():
    return {f:f for f in get_friend_list()}

def specific_friend_menu(friend:str):
    def s_remove_friend(f=friend):
        remove_friend(f)
        return 1
    return do_menu({
        "Remove "+friend:s_remove_friend
    },"Friend "+friend)

def add_friend_menu():
    while True:
        friend = input("Enter the factorio playername to add:\n")
        if re.fullmatch(r"[\w.-]+",friend):
            add_friend(friend)
            return 0
        print("Factorio usernames must only include letters, numbers, periods, and dashs.")
def username_menu():
    update_factorio.get_credentials(False,True)
    return 0

def games_with_friends_menu():
    games=get_filtered_game_list()
    return {game['name']: game['game_id'] for game in games}


if __name__ == "__main__":
    get_game_list()
