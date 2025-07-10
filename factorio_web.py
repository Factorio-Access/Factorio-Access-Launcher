import time
import urllib.parse
import urllib.request
import urllib.error
import urllib.response
import json
import http, http.cookiejar
from collections import defaultdict
from typing import TypedDict, NotRequired, Any, Type
from urllib.parse import quote
from http.client import HTTPSConnection, HTTPConnection, RemoteDisconnected


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
    url = "https://www.factorio.com/get-download/1.1.101/alpha/linux64"
    params = {
        "username": username,
        "token": token,
    }
    with request(append_query(url, params), "HEAD") as response:
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
    """Warning: not thread safe."""
    with request(append_query(url, params)) as response:
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


connection_pool: dict[Type, dict[str, HTTPConnection]] = {
    HTTPConnection: {},
    HTTPSConnection: {},
}


def request(url: str, method="GET"):
    """Warning: not thread safe.
    This function uses a connection pool with a single connection for each requested net location.
    The motivation for this is for mod dependency analysis
    where each mod requires it's own request to get the dependencies.
    Reusing the connection dramatically speeds the results."""
    parts = urllib.parse.urlparse(url)
    assert parts.hostname
    if parts.query:
        url = f"{parts.path}?{parts.query}"
    else:
        url = parts.path
    match parts.scheme:
        case "http":
            con_type = HTTPConnection
        case "https":
            con_type = HTTPSConnection
        case _:
            raise ValueError("Unsupported scheme", parts.scheme)
    pool = connection_pool[con_type]
    for i in range(2):
        if parts.netloc not in pool:
            pool[parts.netloc] = con_type(parts.hostname, parts.port)
        con = pool[parts.netloc]
        try:
            con.request(method, url)
            ret = con.getresponse()
        except RemoteDisconnected:
            del pool[parts.netloc]
        else:
            return ret
    raise Exception("repeated disconnects")


if __name__ == "__main__":
    parts = urllib.parse.urlparse(
        "https://mods.factorio.com:12345/hi/hello?woot=5&woot=6#butt"
    )
    c = HTTPSConnection("mods.factorio.com")
    c.set_debuglevel(1)
    c.request("GET", "/api/mods")
    r1 = c.getresponse()
    c.request("GET", "/api/mods?page=2")
    print(r1.closed)
    with r1 as fp:
        resp1 = json.load(fp)
    print(r1.closed)
    r2 = c.getresponse()
    with r2 as fp:
        resp2 = json.load(fp)
    print("done", len(resp1) + len(resp2))
