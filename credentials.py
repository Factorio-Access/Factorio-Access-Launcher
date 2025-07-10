from player_data import get_player_data, save_player_data
import factorio_web
from factorio_web import sign_in_via_api, Credentials, Bad_Credentials


class NotLoggedIn(Exception):
    """Exception raised when the user is not logged in."""


def set_credentials(credentials: Credentials):
    data = get_player_data()
    data["service-username"] = credentials["username"]
    data["service-token"] = credentials["token"]
    save_player_data(data)


def get_credentials() -> Credentials:
    data = get_player_data()
    if data["service-username"] == "" or data["service-token"] == "":
        raise NotLoggedIn("Not logged in")
    return {
        "username": data["service-username"],
        "token": data["service-token"],
    }


def sign_in_via_web_api(username: str, password: str) -> Credentials:
    response = sign_in_via_api(username, password)
    credentials: Credentials = {
        "username": response["username"],
        "token": response["token"],
    }
    set_credentials(credentials)
    return credentials


def sign_in_with_credentials(username: str, token: str) -> Credentials:
    credentials: Credentials = {
        "username": username,
        "token": token,
    }
    set_credentials(credentials)
    return credentials


def check_credentials(c: Credentials):
    return factorio_web.check_credentials(c["username"], c["token"])


def get_json_with_credentials(url: str, params: dict[str, object] = {}) -> dict:
    """Open a URL with credentials and return the JSON response."""
    p = params.copy()
    p.update(**get_credentials())
    return factorio_web.get_json(url, p)
