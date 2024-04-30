import http.server
from http import HTTPStatus
import json
import urllib.parse
from pathlib import Path, PurePath
from typing import Union
from html.parser import HTMLParser
import io
import sys
import re

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from translations import translate, check_lang


class MyHTMLParser(HTMLParser):
    def __init__(self, out: io.StringIO, *args) -> None:
        self.output_buf = out
        super().__init__(*args, convert_charrefs=False)

    # Overridable -- finish processing of start+end tag: <tag.../>
    def handle_startendtag(self, tag, attrs):
        self.output_buf.write(tag)

    # Overridable -- handle start tag
    def handle_starttag(self, tag, attrs):
        self.output_buf.write(f"<{tag}{attrs}")

    # Overridable -- handle end tag
    def handle_endtag(self, tag):
        self.output_buf.write(tag)

    # Overridable -- handle character reference
    def handle_charref(self, name):
        self.output_buf.write(name)

    # Overridable -- handle entity reference
    def handle_entityref(self, name):
        self.output_buf.write(name)

    # Overridable -- handle data
    def handle_data(self, data):
        try:
            localised_str = json.loads(data)
        except:
            localised_str = data
        else:
            localised_str = translate(localised_str)
        self.output_buf.write(localised_str)

    # Overridable -- handle comment
    def handle_comment(self, data):
        pass

    # Overridable -- handle declaration
    def handle_decl(self, decl):
        self.output_buf.write(f"<!{decl}>")

    # Overridable -- handle processing instruction
    def handle_pi(self, data):
        raise ValueError("Can't handle processing instruction")

        print("Encountered some data  :", data)


_root = Path(__file__).parent.joinpath("web_root").resolve()
assert _root.is_dir()


def translate_json(m: re.Match[bytes]) -> bytes:
    try:
        loc_str = json.loads(m[0][1:-1])
    except json.JSONDecodeError:
        return m[0]
    return (">" + translate(loc_str) + "<").encode()


class FA_handler(http.server.SimpleHTTPRequestHandler):
    resp = json.dumps({"test": "woot"}).encode("utf8")

    def __init__(self, request, client_address, server) -> None:
        super().__init__(request, client_address, server, directory=_root)

    def send_file(self, path: Path):
        self.send_header("Content-Type", "text/html; charset=UTF-8")
        with path.open("br") as fp:
            buff = fp.read()
            # todo get more if nessisary
            buff = re.sub(rb">\[[^<>]*\]<", translate_json, buff)
            self.send_header("Content-Length", str(len(buff)))
            self.end_headers()
            if self.command == "GET":
                self.wfile.write(buff)
            return

    def do_OPTIONS(self):
        path = self.check_path()
        if not path:
            return
        self.send_response(HTTPStatus.OK)
        # self.send_header("Access-Control-Allow-Origin","https://mods.factorio.com")
        self.send_header("Content-Length", str(0))
        self.end_headers()

    def do_HEAD(self) -> None:
        path = self.check_path()
        if not path:
            return
        if isinstance(path, urllib.parse.ParseResult):
            self.api_send_head()
            return
        self.send_file(path)
        # return super().do_HEAD()

    def do_GET(self) -> None:
        path = self.check_path()
        if not path:
            return
        if isinstance(path, urllib.parse.ParseResult):
            self.api_send_head()
            self.wfile.write(self.resp)
            return
        self.send_response(HTTPStatus.OK)
        self.send_file(path)
        # return super().do_GET()

    def do_POST(self) -> None:
        path = self.check_path()
        if not path:
            return
        if isinstance(path, Path):
            self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
            self.end_headers()
            return
        self.api_send_head()
        self.wfile.write(self.resp)

    def check_path(self) -> Union[Path, urllib.parse.ParseResult, None]:
        path = urllib.parse.urlparse(self.path, "http", False)
        if path.path.startswith("/api/"):
            return path
        rel = PurePath("." + path.path)
        maybe_file = _root.joinpath(rel).resolve()
        if maybe_file.is_relative_to(_root) and maybe_file.is_file():
            return maybe_file
        self.send_response(HTTPStatus.NOT_FOUND)
        self.send_file(_root.joinpath("404.html"))
        return False

    def api_send_head(self):
        self.send_response(HTTPStatus.OK)
        self.send_header("Access-Control-Allow-Origin", "https://mods.factorio.com")
        self.send_header("Content-type", "application/json")
        self.send_header("Content-Length", str(len(self.resp)))
        self.end_headers()


check_lang()

server = http.server.HTTPServer(("127.0.0.1", 34197), FA_handler)
server.serve_forever()
