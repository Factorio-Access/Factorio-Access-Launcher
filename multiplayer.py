import os
import json
from typing import Final
import re

import config
import update_factorio
import fa_paths
import __main__ as main

__ACCESS_LIST_PATH : Final[str] = os.path.join(fa_paths.WRITE_DIR,"server-whitelist.json")

def get_game_list():
    cred = update_factorio.get_credentials()
    url=f"https://multiplayer.factorio.com/get-games?username={cred['username']}&token={cred['token']}"
    with update_factorio.opener.open(url) as fp:
        games = json.load(fp)
        players=set()
        for game in games:
            players|=set(game.get("players",[]))
        with open("players",'w') as fp:
            fp.writelines(player+"\n" for player in players)
        return games

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


def multiplayer_launch(game):
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
    return main.launch_with_params([],announce_press_e=True)


def get_username_menu():
    return "Username: "+update_factorio.get_player_data()["service-username"]

def get_friends_menu():
    return {f:f for f in get_friend_list()}

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
    return {game['name']: game['host_address'] for game in games}


if __name__ == "__main__":
    get_game_list()
