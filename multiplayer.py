import os
import json
from typing import Final
import re

import config
import player_data
import fa_paths
import fa_menu
import launch_and_monitor
from credentials import get_json_with_credentials
from factorio_web import get_json

__ACCESS_LIST_PATH = fa_paths.WRITE_DIR.joinpath("server-whitelist.json")


def get_game_list():
    return get_json_with_credentials("https://multiplayer.factorio.com/get-games")


def get_game(game_id):
    url = f"https://multiplayer.factorio.com/get-game-details/{game_id}"
    return get_json(url)


def get_filtered_game_list():
    games = get_game_list()
    friends = set(get_friend_list())
    return [game for game in games if set(game.get("players", [])) & friends]


def get_friend_list():
    try:
        with __ACCESS_LIST_PATH.open(encoding="utf8") as fp:
            return json.load(fp)
    except:
        return []


def add_friend(friend: str):
    with __ACCESS_LIST_PATH.open("a+", encoding="utf8", newline="") as fp:
        fp.seek(0)
        try:
            friends: list[str] = json.load(fp)
        except:
            friends = []
        friends.append(friend)
        fp.seek(0)
        fp.truncate()
        json.dump(friends, fp, indent=2)


def remove_friend(friend: str):
    with __ACCESS_LIST_PATH.open("r+", encoding="utf8", newline="") as fp:
        friends = set(json.load(fp))
        friends.remove(friend)
        fp.seek(0)
        fp.truncate()
        json.dump(list(friends), fp, indent=2)


def multiplayer_join(game_id):
    game = get_game(game_id)
    if fa_paths.BIN.count("steam") and "steam_id" in game:
        launch_and_monitor.launch_with_params(
            ["--join-game-by-steam-id", game["steam_id"]]
        )
    else:
        launch_and_monitor.connect_to_address(game["host_address"])


def multiplayer_host(game):
    with config.current_conf as conf:
        if conf.multiplayer_lobby.name == "":
            conf.multiplayer_lobby.name = "FactorioAccessDefault"
        player = player_data.get_player_data()
        player["last-played"] = {
            "type": player_data.LastPlayedType.HOST,
            "host-settings": {
                "server-game-data": {
                    "visibility": {
                        "public": bool(conf.multiplayer_lobby.visibility_public),
                        "steam": bool(conf.multiplayer_lobby.visibility_steam),
                        "lan": bool(conf.multiplayer_lobby.visibility_lan),
                    },
                    "name": str(conf.multiplayer_lobby.name),
                    "description": str(conf.multiplayer_lobby.description),
                    "max_players": int(conf.multiplayer_lobby.max_players),
                    "game_time_elapsed": 150,
                    "has_password": conf.multiplayer_lobby.password != "",
                },
                "server-username": player["service-username"],
                "autosave-interval": int(conf.other.autosave_interval),
                "afk-autokick-interval": int(conf.multiplayer_lobby.afk_auto_kick),
            },
            "save-name": game[:-4],
        }
    player_data.save_player_data(player)
    return launch_and_monitor.launch_with_params(
        [], announce_press_e=True, tweak_modified=os.path.join(fa_paths.SAVES, game)
    )


class config_toggle(fa_menu.setting_menu_bool):
    def __init__(self, setting: tuple[str, str], title) -> None:
        self.setting = setting
        super().__init__(title)

    def val_to_string(self, *args):
        self.val = config.current_conf.get_setting(*self.setting) == "true"
        return super().val_to_string(*args)

    def set_val(self, val, *args):
        val_str = "true" if val else "false"
        config.current_conf.set_setting(*self.setting, val_str)
        return super().set_val(val, *args)


class host_settings_menu(fa_menu.Menu):
    def __init__(self):
        setting_data = {
            "visibility-public": "gui-multiplayer-lobby.game-visibility-public",
            "visibility-lan": "gui-multiplayer-lobby.game-visibility-LAN",
            "visibility-steam": "gui-multiplayer-lobby.game-visibility-steam",
            "enable-whitelist": "fa-l.access-list-enabled",
            "verify-user-identity": "gui-multiplayer-lobby.verify-user-identity",
        }
        items = []
        for key, name in setting_data.items():
            setting_key = ("multiplayer-lobby", key)
            items.append(config_toggle(setting_key, (name,)))
        super().__init__(title=("gui-multiplayer-lobby.title",), items=items)

    def __call__(self, *args):
        with config.current_conf:
            return super().__call__(*args)


def get_username_menu():
    try:
        player = player_data.get_player_data()
    except player_data.NoPlayerData:
        player = {"service-username": "None"}
    return [("Username: " + player["service-username"],)]


def get_friends_menu():
    return [(f, f) for f in get_friend_list()]


def remove_friend_title(friend: str, *args):
    return [(f"Remove {friend} from your friend list",)]


def add_friend_menu():
    while True:
        friend = input("Enter the factorio player name to add:\n")
        if re.fullmatch(r"[\w.-]+", friend):
            add_friend(friend)
            return 0
        print(
            "Factorio usernames must only include letters, numbers, periods, and dashes."
        )


friend_list = {
    "Add": add_friend_menu,
    get_friends_menu: {remove_friend_title: remove_friend},
}


def games_with_friends_menu():
    games = get_filtered_game_list()
    return [(game["name"], game["game_id"]) for game in games]


if __name__ == "__main__":
    get_game_list()
