from collections.abc import Iterable
import json
import re
import zipfile
import pathlib
from urllib import parse, error
from collections import defaultdict
from typing import Iterator, Union, TypedDict
from enum import StrEnum
from functools import reduce

import config
from fa_paths import MODS, READ_DIR, FACTORIO_VERSION
from fa_arg_parse import d_print
from update_factorio import download, get_credentials, opener

_mod_portal = "https://mods.factorio.com"


class info_json(TypedDict):
    name: str
    version: str
    dependencies: list[str]


class Release(TypedDict):
    download_url: str  # 	Path to download for a mod. starts with "/download" and does not include a full url. See #Downloading Mods
    file_name: str  # 	The file name of the release. Always seems to follow the pattern "{name}_{version}.zip"
    info_json: info_json  # A copy of the mod's info.json file, only contains factorio_version in short version, also contains an array of dependencies in full version
    released_at: str  # 	String(ISO 8601)	ISO 8601 for when the mod was released.
    version: (
        str  # g	The version string of this mod release. Used to determine dependencies.
    )
    sha1: str  # 	String	The sha1 key for the file


class PortalResult(TypedDict):
    downloads_count: int  # Number of downloads.
    name: str  # The mod's machine-readable ID string.
    owner: str  # The Factorio username of the mod's author.
    releases: list[
        Release
    ]  # A list of different versions of the mod available for download.
    summary: str  # A shorter mod description.
    title: str  # The mod's human-readable name.


class Pagination(TypedDict):
    count: int  # Total number of mods that match your specified filters.
    links: dict  # Utility links to mod portal api requests, preserving all filters and search queries.
    page: int  # The current page number.
    page_count: int  # The total number of pages returned.
    page_size: int  # The number of results per page.


class PortalListResult(TypedDict):
    pagination: Pagination
    results: list[PortalResult]


class mod_version(tuple):
    def __new__(cls, version: str):
        ver = [0, 0, 0]
        for i, val in enumerate(version.split(".", 2)):
            ver[i] = int(val)
        return super().__new__(cls, ver)

    def __repr__(self) -> str:
        return ".".join(str(n) for n in self)


MIN_MOD_VERSION = mod_version("0")
MAX_MOD_VERSION = mod_version("65535.65535.65535")


class DependencyType(StrEnum):
    CONFLICT = "!"
    HIDDEN_OPTIONAL = "(?)"
    OPTIONAL = "?"
    UNORDERED = "~"
    NORMAL = ""

    def __lt__(self, other):
        return list(DependencyType).index(self) < list(DependencyType).index(other)

    def __gt__(self, other):
        return list(DependencyType).index(self) > list(DependencyType).index(other)

    def __le__(self, other):
        return list(DependencyType).index(self) <= list(DependencyType).index(other)

    def __ge__(self, other):
        return list(DependencyType).index(self) >= list(DependencyType).index(other)


ver_comp = tuple[mod_version, int]


class IncompatibleDependencies(ValueError):
    pass


class dependency(object):
    __types = "|".join([re.escape(t) for t in DependencyType])
    __re = re.compile(rf"({__types})\s*(\S+)(?:\s*([><=]+)\s*(\d+\.\d+(?:\.\d+)?))?")

    def __init__(
        self, type: DependencyType, name: str, min_ver: ver_comp, max_ver: ver_comp
    ):
        self.type = type
        self.name = name
        self.min = min_ver
        self.max = max_ver

    @classmethod
    def from_str(cls, dep: str):
        m = cls.__re.fullmatch(dep)
        if not m:
            raise ValueError(f"Unmatched mod dependency {dep}")
        name = m[2]
        type = DependencyType(m[1])
        # the second values of the tuples allow for < and > to be handled with <= and >= so we don't need branching
        min = (MIN_MOD_VERSION, 0)
        max = (MAX_MOD_VERSION, 0)
        if type == "!":
            max = (MIN_MOD_VERSION, -1)
        elif not m[4]:
            pass
        else:
            ver = mod_version(m[4])
            match m[3]:
                case "<":
                    max = (ver, -1)
                case "<=":
                    max = (ver, 0)
                case "<":
                    min = (ver, 1)
                case "<=":
                    min = (ver, 0)
                case "=":
                    min = max = (ver, 0)
        return cls(type, name, min, max)

    def meets(self, other: mod_version):
        return self.min <= (other, 0) <= self.max

    def __lt__(self, other):
        order = list(DependencyType)
        return order.index(self.type) < order.index(other.type)

    def __add__(self, other):
        if not other:
            return self
        assert isinstance(other, dependency)
        if self.name != other.name:
            raise ValueError(f"Mod names must match {self.name}!={other.name}")
        a, b = sorted([self, other])
        if a.type == DependencyType.CONFLICT:
            if b.type >= DependencyType.UNORDERED:
                raise IncompatibleDependencies(
                    f"Dependencies incompatible", self, other
                )
            return a
        # at this point neither is a conflict
        n_type = max(a.type, b.type)
        n_min = max(a.min, b.min)
        n_max = min(a.max, b.max)
        if n_min < n_max:
            if b.type <= DependencyType.OPTIONAL:
                return dependency(
                    DependencyType.CONFLICT,
                    a.name,
                    (MIN_MOD_VERSION, 0),
                    (MIN_MOD_VERSION, -1),
                )
            raise IncompatibleDependencies(f"Dependencies incompatible", self, other)
        return dependency(n_type, a.name, n_min, n_max)


class Dependencies(dict):
    def __init__(self, deps=None):
        super().__init__(self)
        if deps:
            self += deps
        pass

    def __iadd__(self, deps):
        if isinstance(deps, dependency):
            if deps.name in self:
                self[deps.name] += deps
            else:
                self[deps.name] = deps
            return self
        if isinstance(deps, str):
            self += dependency.from_str(deps)
            return self
        for dep in deps:
            self += dep
        return self


class mod(object):
    info: info_json

    def __init__(self, info: info_json) -> None:
        self.info = info
        self.dependencies = Dependencies(info["dependencies"])
        self.version = mod_version(info["version"])
        self.name = info["name"]


class installed_mod(mod):
    def __init__(self, path: Union[zipfile.Path, pathlib.Path]) -> None:
        if path.is_file():
            if not zipfile.is_zipfile(path):
                raise ValueError(f"non zip file {path} failed mod init")
            self.folder_path = next(zipfile.Path(path).iterdir())
        else:
            self.folder_path = path
        info_path = self.folder_path.joinpath("info.json")
        if not info_path.is_file():
            raise ValueError(f"no info file in {self.folder_path}; failed mod init")
        with info_path.open(encoding="utf8") as fp:
            i: info_json = json.load(fp)
        if path.name == "core":
            i["version"] = FACTORIO_VERSION
        re_name = f"{i['name']}(_{i['version']})?(.zip)?"
        if not re.fullmatch(re_name, path.name):
            raise ValueError(
                f"""Mod path mismatch:
   mod path: {path}
   name:{path.name}
   re:{re_name}"""
            )
        super().__init__(i)

    @staticmethod
    def _iter_files_sub(
        parts: list[Union[str, re.Pattern]], path: Union[zipfile.Path, pathlib.Path]
    ):
        if not path.exists():
            return
        if not parts:
            if path.is_file():
                yield path
            return
        if not path.is_dir():
            return
        part = parts[0]
        if isinstance(part, str):
            yield from installed_mod._iter_files_sub(parts[1:], path.joinpath(part))
            return
        for path_part in path.iterdir():
            if part.fullmatch(path_part.name):
                yield from installed_mod._iter_files_sub(parts[1:], path_part)

    def iterate_mods_files(self, parts: list[Union[str, re.Pattern]]):
        yield from self._iter_files_sub(parts, self.folder_path)


class portal_mod(mod):
    def __init__(self, release: Release) -> None:
        super().__init__(release["info_json"])
        self.release = release


class UnresolvedModDependency(Exception):
    pass


class __mod_manager(object):
    MOD_LIST_FILE = MODS.joinpath("mod-list.json")

    def __init__(self) -> None:
        self.dict = None
        with config.current_conf:
            self.new_enabled = config.other.enable_new_mods == "true"

    def __enter__(self) -> None:
        assert self.dict == None, "Already in a with statement"
        with open(self.MOD_LIST_FILE, "r", encoding="utf8") as fp:
            data = json.load(fp)
        self.dict = {m["name"]: m for m in data["mods"]}

        self.modified = False
        self.by_name_version: defaultdict[str, dict[mod_version, mod]] = defaultdict(
            dict
        )
        for mod_path in self._iterate_over_all_mod_paths():
            self.add_installed_mod(mod_path)

        pre_size = len(self.dict)
        self.dict = {
            name: m for name, m in self.dict.items() if name in self.by_name_version
        }
        if len(self.dict) != pre_size:
            self.modified = True

    def __exit__(self, *args) -> None:
        if self.modified:
            data = {"mods": [m for m in self.dict.values()]}
            with open(self.MOD_LIST_FILE, "w", encoding="utf8") as fp:
                json.dump(data, fp, ensure_ascii=False, indent=2)
        self.dict = None

    def enabled(self) -> list[str]:
        return [name for name, m in self.dict.items() if m["enabled"]]

    def set_enabled(self, name: str, val: bool) -> None:
        assert self.dict
        self.dict[name]["enabled"] = val
        self.modified = True

    def enable(self, name) -> None:
        self.set_enabled(name, True)

    def disable(self, name) -> None:
        self.set_enabled(name, False)

    def select_version(self, name, version):
        self.dict[name]["version"] = version
        self.modified = True

    def find_dep(self, dep: dependency):
        if dep.type == DependencyType.CONFLICT:
            return True
        if dep.name not in self.by_name_version:
            return False
        vers = self.by_name_version[dep.name]
        ops = [ver for ver in vers.keys() if dep.meets(ver)]
        if ops:
            return vers[max(ops)]
        return False

    def check_dep(self, dep: dependency, do_optional=False):
        if dep.type == DependencyType.CONFLICT:
            if dep.name in self.dict:
                return not self.dict[dep.name]["enabled"]
            return True
        if dep.name in self.dict:
            current = self.dict[dep.name]
            if "version" in current:
                current_ver = mod_version(current["version"])
            else:
                current_ver = max(self.by_name_version[dep.name])
            return dep.meets(current_ver)
        if dep.type == "(?)" or (dep.type == "?" and not do_optional):
            return True
        return False

    def force_dep(self, dep: dependency, do_optional=False):
        if dep.type == "!":
            if dep.name in self.dict:
                self.dict[dep.name]["enabled"] = False
            return True
        if dep.name in self.dict:
            current = self.dict[dep.name]
            if "version" in current:
                current_ver = mod_version(current["version"])
            else:
                current_ver = max(self.by_name_version[dep.name])
            if dep.meets(current_ver):
                return True
            ops = [ver for ver in self.by_name_version[dep.name] if dep.meets(ver)]
            if ops:
                current["enabled"] = True
                current["version"] = str(ops[-1])
                return True
            if dep.type == "(?)" or (dep.type == "?" and not do_optional):
                self.dict[dep.name]["enabled"] = False
                return True
        if dep.type == "(?)" or (dep.type == "?" and not do_optional):
            return True
        return self.install_mod(dep)

    def install_mod(self, dep: dependency):
        with opener.open(f"{_mod_portal}/api/mods/{dep.name}") as fp:
            info: PortalResult = json.load(fp)
        ops = [r for r in info["releases"] if dep.meets(mod_version(r["version"]))]
        if not ops:
            raise ValueError(f"No mods on portal matching dependency:{dep}")
        self.download_mod(ops[-1])

    def download_mod(self, release):
        cred = get_credentials()
        url = _mod_portal + release["download_url"] + "?" + parse.urlencode(cred)
        new_path = MODS.joinpath(release["file_name"])
        download(url, new_path)
        self.add_installed_mod(new_path)

    def add_installed_mod(self, mod_path):
        try:
            m = installed_mod(mod_path)
        except Exception as e:
            d_print(e)
            return
        self.by_name_version[m.name][m.version] = m  # TODO: check duplicates?
        if m.name not in self.dict and m.name != "core":
            self.dict[m.name] = {"name": m.name, "enabled": self.new_enabled}
            self.modified = True

    def add_info_for_mods(self, mod_names: list[str]):
        args = {"namelist": ",".join(mod_names)}
        encoded_args = parse.urlencode(args)
        with opener.open(f"{_mod_portal}/api/mods/?{encoded_args}") as fp:
            info: PortalListResult = json.load(fp)
        for r in info["results"]:
            self.add_info_for_mod(r)

    def add_info_for_mod(self, result: PortalResult):
        for release in result["releases"]:
            self.add_info_for_release(release)

    def add_info_for_release(self, release: Release):
        m = portal_mod(release)
        self.by_name_version[m.name][m.version] = m

    def expand_dependencies(self, deps: set[dependency]):
        collected: set[dependency] = set()
        progress = True
        connection_issues = False
        while progress:
            expanding = deps
            deps: set[dependency] = set()
            progress = False
            while expanding:
                dep = expanding.pop()
                if dep.type <= DependencyType.OPTIONAL:
                    progress == True
                    collected.add(dep)
                    continue
                m = self.find_dep(dep)
                if m is False:
                    deps.add(dep)
                    continue
                new_deps = set(m.dependencies)
                new_deps -= collected
                new_deps -= deps
                expanding |= new_deps
            if not deps:
                break
            self.add_info_for_mods([d.name for d in deps])
        if deps:
            raise UnresolvedModDependency(deps)
        return Dependencies(collected)

    fancy = re.compile(r"[*.?()\[\]]")

    def get_mod_path_parts(self, path: Union[zipfile.Path, pathlib.Path]):
        if isinstance(path, pathlib.Path):
            try:
                return path.relative_to(MODS).parts
            except:
                pass
            return path.relative_to(READ_DIR).parts
        parts = []
        while isinstance(path.parent, zipfile.Path):
            parts.append(path.name)
            path = path.parent
        return tuple(parts[::-1])

    def _iterate_over_all_mod_paths(self) -> Iterator[pathlib.Path]:
        for base_core in ["core", "base"]:
            yield READ_DIR.joinpath(base_core)
        yield from MODS.iterdir()

    def iter_mods(
        self, require_enabled=True, mod_filter: re.Pattern = None
    ) -> Iterator[mod]:
        for m in self.dict.values():
            if m["enabled"] or not require_enabled:
                name = m["name"]
                if mod_filter and not mod_filter.fullmatch(name):
                    continue
                ver = "version" in m and m["version"] or max(self.by_name_version[name])
                yield self.by_name_version[name][ver]

    def iter_mod_files(
        self, inner_re_path: str, require_enabled=True, mod_filter: re.Pattern = None
    ) -> Iterator[Union[zipfile.Path, pathlib.Path]]:
        parts = inner_re_path.split("/")
        parts = [
            part if not self.fancy.search(part) else re.compile(part) for part in parts
        ]
        for mod in self.iter_mods(require_enabled, mod_filter):
            yield from mod.iterate_mods_files(parts)


mod_manager = __mod_manager()


if __name__ == "__main__":
    test = [
        DependencyType.CONFLICT,
        DependencyType.HIDDEN_OPTIONAL,
        DependencyType.CONFLICT,
        DependencyType.NORMAL,
    ]
    s_test = list(sorted(test))
    print(test, s_test)
    test.sort(key=lambda x: list(DependencyType).index(x))
    print(test)
    print(DependencyType.NORMAL <= DependencyType.OPTIONAL)
    print(list(DependencyType))
    print(dependency.from_str("! stop >= 3.4.5").meets(mod_version("3.4.5")))
    with mod_manager:
        pass
