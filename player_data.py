from typing import TypedDict, NotRequired, Literal, Any
from enum import StrEnum
import json

from fa_paths import PLAYER_DATA


class NoPlayerData(FileNotFoundError):
    pass


class Difficulty(StrEnum):
    HARD = "hard"
    NORMAL = "normal"
    EASY = "easy"


class Status(StrEnum):
    Completed = "completed"
    CompletedWithoutTutorial = "completed-without-tutorial"
    Suggested = "suggested"
    Locked = "locked"
    Unlocked = "unlocked"


class TipData(TypedDict):
    status: Status
    elapsed: NotRequired[int]
    conditions: NotRequired[list[dict]]


class LastPlayedType(StrEnum):
    HOST = "hosted-multiplayer"
    JOIN = "TBD-join"
    SOLO = "TBD-solo"


class LastPlayed(TypedDict):
    type: LastPlayedType


class Visibility(TypedDict):
    public: NotRequired[bool]
    steam: NotRequired[bool]
    lan: NotRequired[bool]


class ServerGameData(TypedDict):
    visibility: Visibility
    name: str
    description: str
    max_players: NotRequired[int]
    game_time_elapsed: NotRequired[int]
    has_password: bool
    server_id: NotRequired[str]


HostSettings = TypedDict(
    "HostSettings",
    {
        "server-game-data": ServerGameData,
        "server-username": str,
        "autosave-interval": int,
        "afk-autokick-interval": int,
        "required-verification": NotRequired[bool],
        "enable-authserver-side-bans": NotRequired[bool],
    },
)

LastPlayedHost = TypedDict(
    "LastPlayedHost",
    {
        "type": Literal[LastPlayedType.HOST],
        "host-settings": HostSettings,
        "save-name": str,
    },
)


class MultiplayerConnection(TypedDict):
    address: str


class ShortCutBarItem(TypedDict):
    name: str
    docked: bool
    enabled: bool


class LastPlayedVersion(TypedDict):
    game_version: str
    build_version: int
    build_mode: str
    platform: str


PlayerData = TypedDict(
    "PlayerData",
    {
        "available-campaign-levels": dict[str, dict[str, Difficulty]],
        "finished-campaigns": dict[str, Difficulty],
        "tips": dict[str, TipData],
        "console-history": list[str],
        "last-played": LastPlayedHost,
        "latest-multiplayer-connections": list[MultiplayerConnection],
        "service-username": str,
        "service-token": str,
        "shortcut-bar": list[ShortCutBarItem],
        "editor-lua-snippets": list[Any],
        "last-played-version": LastPlayedVersion,
        "blueprint-view": str,
        "main-menu-simulations-played": list[str],
    },
)


def get_player_data():
    try:
        with PLAYER_DATA().open(encoding="utf8") as fp:
            data: PlayerData = json.load(fp)
    except FileNotFoundError:
        raise NoPlayerData("Player data file not found.")
    return data


def save_player_data(data: PlayerData):
    try:
        with PLAYER_DATA().open("w", encoding="utf8") as fp:
            json.dump(data, fp, indent=2)
    except FileNotFoundError:
        raise NoPlayerData("Player data file not found.")
