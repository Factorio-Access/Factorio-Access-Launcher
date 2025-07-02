import time
import urllib.parse
import urllib.request
import urllib.error
import urllib.response
import json
import http, http.cookiejar
from typing import TypedDict, NotRequired, Any
from urllib.parse import quote

LOGIN_API = "https://auth.factorio.com/api-login"


class Bad_Credentials(Exception):
    """Exception raised when the credentials are invalid."""


opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
    urllib.request.HTTPSHandler(
        debuglevel=0
    ),  # change to 1 for testing 0 for production
)
# cSpell:words cloudfare addheaders KHTML
# cloudfare rejects the default user agent
opener.addheaders = [
    (
        "User-agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
    )
]


class Credentials(TypedDict):
    username: str
    token: str


class LoginResponse(Credentials):
    error: NotRequired[str]
    message: NotRequired[str]


def sign_in_via_api(username: str, password: str) -> Credentials:
    params = {
        "username": username,
        "password": password,
        "api_version": "4",
        "require_game_ownership": "true",
    }
    encoded_params = urllib.parse.urlencode(params).encode("utf-8")
    with opener.open(LOGIN_API, encoded_params) as response:
        json_resp: LoginResponse = json.load(response)
    if "error" in json_resp:
        raise Bad_Credentials(json_resp["error"] + " " + json_resp.get("message", ""))
    if "username" not in json_resp or "token" not in json_resp:
        raise Bad_Credentials("Invalid response from server")
    return json_resp


class NoRedirection(urllib.request.HTTPErrorProcessor):
    def http_response(self, request, response):
        return response

    https_response = http_response


def check_credentials(username: str, token: str) -> bool:
    """Check if the provided credentials are valid."""
    no_re_opener = urllib.request.build_opener(NoRedirection)
    no_re_opener.addheaders = opener.addheaders
    url = "https://www.factorio.com/get-download/1.1.101/alpha/linux64?"
    url += urllib.parse.urlencode(
        {
            "username": username,
            "token": token,
        }
    )
    req = urllib.request.Request(url, method="HEAD")
    with no_re_opener.open(req) as response:
        if response.status == 302:
            return True
        elif response.status == 403:
            return False
        raise ValueError(f"Unexpected response: {response.status}")


def append_query(url: str, params: dict[str, Any] = {}):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return url


def get_json(url: str, params: dict[str, Any] = {}):
    with opener.open(append_query(url, params)) as response:
        return json.load(response)


def download(url, filename, params: dict[str, Any] = {}):
    url = append_query(url, params)
    with open(filename, "wb") as fp, opener.open(url) as dl:
        # print(f"saving {url} to {filename}")
        length = dl.getheader("content-length")
        buff_size = 4096

        if length:
            length = int(length)
            if length > 4096 * 20:
                print(f"Downloading {length} bytes")

        bytes_done = 0
        last_percent = -1
        last_reported = time.time()
        while True:
            buffer = dl.read(buff_size)
            if not buffer:
                break
            fp.write(buffer)
            bytes_done += len(buffer)
            if length:
                percent = bytes_done * 100 // length
                if percent > last_percent and time.time() >= 5 + last_reported:
                    print(f"{percent}%")
                    last_percent = percent
                    last_reported = time.time()
        if length and length > 4096 * 20:
            print("Done")
