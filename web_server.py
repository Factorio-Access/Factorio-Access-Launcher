import http.server
from http import HTTPStatus
import json
import urllib.parse
from pathlib import Path, PurePath
from typing import Union
import html
from html.parser import HTMLParser
import io
import sys
import re


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


_root = Path(__file__).parent.joinpath("web", "web_root").resolve()
assert _root.is_dir()


def translate_json(m: re.Match[bytes]) -> bytes:
    try:
        loc_str = json.loads(m[0][1:-1])
    except json.JSONDecodeError:
        return m[0]
    return (">" + html.escape(translate(loc_str)) + "<").encode()


class FA_handler(http.server.SimpleHTTPRequestHandler):
    resp = json.dumps({"test": "woot"}).encode("utf8")

    def __init__(self, request, client_address, server) -> None:
        super().__init__(request, client_address, server, directory=_root)

    ext_map = {
        ".html": "text/html; charset=UTF-8",
        ".js": "text/javascript; charset=UTF-8",
        ".css": "text/css; charset=UTF-8",
        ".ico": "image/vnd.microsoft.icon",
    }

    def send_file(self, path: Path):
        ext = path.suffix
        self.send_header("Content-Type", self.ext_map[ext])
        with path.open("br") as fp:
            buff = fp.read()
        if ext == ".html":
            buff = re.sub(rb">\[[^<>]*\]<", translate_json, buff)
        self.send_header("Content-Length", str(len(buff)))
        self.end_headers()
        if self.command == "GET":
            self.wfile.write(buff)

    def do(self):
        path = self.check_path()
        if not path:
            return
        if self.command == "OPTIONS":
            return self.finish_OPTIONS(path)
        if isinstance(path, urllib.parse.ParseResult):
            return self.api_call(path)
        if self.command not in ["GET", "HEAD"]:
            self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
            self.send_header("Content-Length", str(0))
            return
        self.send_response(HTTPStatus.OK)
        return self.send_file(path)

    def finish_OPTIONS(self, path):
        self.send_response(HTTPStatus.OK)
        allowed = ["OPTIONS", "HEAD", "GET"]
        if isinstance(path, urllib.parse.ParseResult):
            allowed += ["POST"]
        self.send_header("Allow", ", ".join(allowed))
        self.send_header("Content-Length", "0")
        self.end_headers()

    def api_call(self, path: urllib.parse.ParseResult):
        pass

    def do_OPTIONS(self):
        self.do()

    def do_HEAD(self) -> None:
        self.do()

    def do_GET(self) -> None:
        self.do()

    def do_POST(self) -> None:
        self.do()

    def check_path(self) -> Union[Path, urllib.parse.ParseResult, None]:
        path = urllib.parse.urlparse(self.path, "http", False)
        if path.path.startswith("/api/"):
            return path
        if path.path.endswith("/index.html"):
            self.send_response(HTTPStatus.MOVED_PERMANENTLY)
            self.send_header("Location", path.path.removesuffix("index.html"))
            self.end_headers()
            return None
        s_path = path.path
        if s_path.endswith("/"):
            s_path += "index.html"
        rel = PurePath("." + s_path)
        maybe_file = _root.joinpath(rel).resolve()
        if maybe_file.is_relative_to(_root) and maybe_file.is_file():
            return maybe_file
        self.send_response(HTTPStatus.NOT_FOUND)
        self.send_file(_root.joinpath("404.html"))
        return None

    def api_send_head(self):
        self.send_response(HTTPStatus.OK)
        self.send_header("Access-Control-Allow-Origin", "https://mods.factorio.com")
        self.send_header("Content-type", "application/json")
        self.send_header("Content-Length", str(len(self.resp)))
        self.end_headers()


check_lang()

server = http.server.HTTPServer(("127.0.0.1", 34197), FA_handler)
server.serve_forever()
