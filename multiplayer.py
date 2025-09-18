import os
import json
from typing import Final
import re

import config
import update_factorio
import fa_paths
import fa_menu
import launch_and_monitor

__ACCESS_LIST_PATH = fa_paths.WRITE_DIR.joinpath("server-whitelist.json")


def get_game_list():
    cred = update_factorio.get_credentials()
    url = f"https://multiplayer.factorio.com/get-games?username={cred['username']}&token={cred['token']}"
    with update_factorio.opener.open(url) as fp:
        games = json.load(fp)
    with open("all_games", "w") as fp:
        json.dump(games, fp, indent=2)
    return games


def get_game(game_id):
    url = f"https://multiplayer.factorio.com/get-game-details/{game_id}"
    with update_factorio.opener.open(url) as fp:
        game = json.load(fp)
    with open(f"game_{game_id}", "w") as fp:
        json.dump(game, fp, indent=2)
    return game


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
    with config.current_conf:
        if config.multiplayer_lobby.name == "":
            config.multiplayer_lobby.name = "FactorioAccessDefault"
        player = update_factorio.get_player_data()
        player["last-played"] = {
            "type": "hosted-multiplayer",
            "host-settings": {
                "server-game-data": {
                    "visibility": {
                        "public": config.multiplayer_lobby.visibility_public,
                        "steam": config.multiplayer_lobby.visibility_steam,
                        "lan": config.multiplayer_lobby.visibility_lan,
                    },
                    "name": config.multiplayer_lobby.name,
                    "description": config.multiplayer_lobby.description,
                    "max_players": config.multiplayer_lobby.max_players,
                    "game_time_elapsed": 150,
                    "has_password": config.multiplayer_lobby.password != "",
                },
                "server-username": player["service-username"],
                "autosave-interval": config.other.autosave_interval,
                "afk-autokick-interval": config.multiplayer_lobby.afk_auto_kick,
                "required-verification": config.multiplayer_lobby.verify_user_identity,
                "enable-authserver-side-bans": config.multiplayer_lobby.enable_authserver_side_bans,
            },
            "save-name": game[:-4],
        }
    update_factorio.set_player_data(player)
    return launch_and_monitor.launch_with_params(
        [], announce_press_e=True, tweak_modified=os.path.join(fa_paths.SAVES, game)
    )


class config_toggle(fa_menu.setting_menu_bool):
    def __init__(self, setting: tuple, title) -> None:
        self.setting = setting
        super().__init__(title)

    def get_items(self, *args):
        return {(self._title, self.val_to_string(*args)): ()}

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
            "visibility-public": "config-output.visibility-public",
            "visibility-lan": "config-output.visibility-lan",
            "visibility-steam": "config-output.visibility-steam",
            "enable-whitelist": "fa-l.access-list-enabled",
            "verify-user-identity": "config-output.verify-user-identity",
        }
        items = []
        for key, name in setting_data.items():
            setting_key = ("multiplayer-lobby", key)
            items.append(config_toggle(setting_key, name))
        super().__init__(title=("gui-multiplayer-lobby.title",), items=items)

    def __call__(self, *args):
        with config.current_conf:
            return super().__call__(*args)


def get_username_menu():
    try:
        player = update_factorio.get_player_data()
    except:
        player = {"service-username": "None"}
    return {"Username: " + player["service-username"]: ()}


def get_friends_menu():
    return {f: (f,) for f in get_friend_list()}


class specific_friend_menu(fa_menu.Menu_var_leaf):
    def get_items(self, my_arg, *args):
        return {"Remove " + my_arg: ()}


def add_friend_menu():
    while True:
        friend = input("Enter the factorio playername to add:\n")
        if re.fullmatch(r"[\w.-]+", friend):
            add_friend(friend)
            return 0
        print(
            "Factorio usernames must only include letters, numbers, periods, and dashs."
        )


friend_list = {
    "Add": add_friend_menu,
    get_friends_menu: {"Remove": specific_friend_menu(remove_friend, "TBD")},
}


def username_menu():
    update_factorio.get_credentials(False, True)
    return 0


def games_with_friends_menu():
    games = get_filtered_game_list()
    return {game["name"]: game["game_id"] for game in games}


if __name__ == "__main__":
    get_game_list()
