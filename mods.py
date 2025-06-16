from collections.abc import Iterable
import json
import re
from zipfile import is_zipfile, Path as zPath
from pathlib import Path
from urllib import parse, error
from collections import defaultdict
from typing import Iterator, Union, TypedDict, NamedTuple, NotRequired
from enum import StrEnum
import traceback

import config
from fa_paths import MODS, READ_DIR, FACTORIO_VERSION
from fa_arg_parse import d_print
from update_factorio import download, opener
from credentials import get_credentials

_mod_portal = "https://mods.factorio.com"

dual_path = zPath | Path


class NotAModPath(ValueError):
    pass


class UnresolvedModDependency(Exception):
    pass


class InfoJson(TypedDict):
    name: str
    version: str
    dependencies: list[str]


class Release(TypedDict):
    download_url: str  # 	Path to download for a mod. starts with "/download" and does not include a full url. See #Downloading Mods
    file_name: str  # 	The file name of the release. Always seems to follow the pattern "{name}_{version}.zip"
    info_json: InfoJson  # A copy of the mod's info.json file, only contains factorio_version in short version, also contains an array of dependencies in full version
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


class ModFileListing(TypedDict):
    name: str
    enabled: bool
    version: NotRequired[str]


class ModFile(TypedDict):
    mods: list[ModFileListing]


class ModVersion(tuple):
    def __new__(cls, version: str):
        ver = [0, 0, 0]
        for i, val in enumerate(version.split(".", 2)):
            ver[i] = int(val)
        return super().__new__(cls, ver)

    def __repr__(self) -> str:
        return ".".join(str(n) for n in self)


MIN_MOD_VERSION = ModVersion("0")
MAX_MOD_VERSION = ModVersion("65535.65535.65535")


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


class VerComp(NamedTuple):
    ver: ModVersion
    epsilon: int  # offsets to emulate e.g < behavior with <=


class IncompatibleDependencies(ValueError):
    pass


class Dependency(object):
    __types = "|".join([re.escape(t) for t in DependencyType])
    __re_raw = rf"({__types})\s*([-\w ]+?)(?:\s*([><=]+)\s*(\d+\.\d+(?:\.\d+)?))?"
    __re = re.compile(__re_raw)

    def __init__(
        self, type: DependencyType, name: str, min_ver: VerComp, max_ver: VerComp
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

        # start with the full range
        min = VerComp(MIN_MOD_VERSION, 0)
        max = VerComp(MAX_MOD_VERSION, 0)
        # and then narrow as specified
        if type == DependencyType.CONFLICT:
            max = VerComp(MIN_MOD_VERSION, -1)
        elif not m[4]:
            # no version restriction
            pass
        else:
            ver = ModVersion(m[4])
            match m[3]:
                case "<":
                    max = VerComp(ver, -1)
                case "<=":
                    max = VerComp(ver, 0)
                case "<":
                    min = VerComp(ver, 1)
                case "<=":
                    min = VerComp(ver, 0)
                case "=":
                    min = max = VerComp(ver, 0)
        return cls(type, name, min, max)

    def meets(self, other: ModVersion):
        # works because of how we set up min and max as tuples
        return self.min <= (other, 0) <= self.max

    def __lt__(self, other):
        order = list(DependencyType)
        return order.index(self.type) < order.index(other.type)

    def __add__(self, other):
        if not other:
            return self
        assert isinstance(other, Dependency)
        if self.name != other.name:
            raise ValueError(f"Mod names must match {self.name}!={other.name}")
        a, b = sorted([self, other])
        if a.type == DependencyType.CONFLICT:
            if b.type >= DependencyType.UNORDERED:
                raise IncompatibleDependencies(self, other)
            return a
        # at this point neither is a conflict
        new_type = max(a.type, b.type)
        new_min = max(a.min, b.min)
        new_max = min(a.max, b.max)
        if new_min < new_max:
            # they have mutually exclusive compatible ranges
            if b.type <= DependencyType.OPTIONAL:
                # both are optional so the mod isn't required
                # therefore this mod is actually conflicting
                return Dependency(
                    DependencyType.CONFLICT,
                    a.name,
                    VerComp(MIN_MOD_VERSION, 0),
                    VerComp(MIN_MOD_VERSION, -1),
                )
            raise IncompatibleDependencies(f"Dependencies incompatible", self, other)
        return Dependency(new_type, a.name, new_min, new_max)


class Dependencies(dict):
    """A collection of dependencies that are all compatible.
    Attempting to add incompatible dependencies raises an error.
    dependencies can be added individually or from an iterable.
    The dependencies to add can be instances or strings."""

    def __init__(self, deps=None):
        super().__init__(self)
        if deps:
            self += deps
        pass

    def __iadd__(self, deps):
        if isinstance(deps, Dependency):
            if deps.name in self:
                self[deps.name] += deps
            else:
                self[deps.name] = deps
            return self
        if isinstance(deps, str):
            self += Dependency.from_str(deps)
            return self
        for dep in deps:
            self += dep
        return self


class Mod(object):
    info: InfoJson

    def __init__(self, info: InfoJson) -> None:
        self.info = info
        if "dependencies" not in info:
            info["dependencies"] = ["base"]
        self.dependencies = Dependencies(info["dependencies"])
        self.version = ModVersion(info["version"])
        self.name = info["name"]


class InstalledMod(Mod):
    def __init__(self, path: dual_path) -> None:
        if path.is_file():
            if not is_zipfile(str(path)):
                raise NotAModPath(path)
            self.folder_path = next(zPath(str(path)).iterdir())
        else:
            self.folder_path = path
        info_path = self.folder_path.joinpath("info.json")
        if not info_path.is_file():
            raise NotAModPath(self.folder_path)
        with info_path.open(encoding="utf8") as fp:
            i: InfoJson = json.load(fp)
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
    def _iter_files_sub(parts: list[str | re.Pattern], path: dual_path):
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
            yield from InstalledMod._iter_files_sub(parts[1:], path.joinpath(part))
            return
        for path_part in path.iterdir():
            if part.fullmatch(path_part.name):
                yield from InstalledMod._iter_files_sub(parts[1:], path_part)

    def iterate_mods_files(self, parts: list[Union[str, re.Pattern]]):
        yield from self._iter_files_sub(parts, self.folder_path)


class PortalMod(Mod):
    def __init__(self, release: Release) -> None:
        super().__init__(release["info_json"])
        self.release = release


class ModManager(object):
    MOD_LIST_FILE = MODS / "mod-list.json"

    def __init__(self) -> None:
        with config.current_conf as conf:
            self.new_enabled = conf.other.enable_new_mods == "true"
        try:
            with open(self.MOD_LIST_FILE, "r", encoding="utf8") as fp:
                data: ModFile = json.load(fp)
        except FileNotFoundError:
            data = {"mods": []}
        self.dict = {m["name"]: m for m in data["mods"]}
        self.modified = False
        self.by_name_version: defaultdict[str, dict[ModVersion, Mod]] = defaultdict(
            dict
        )
        for mod_path in self._iterate_over_all_mod_paths():
            try:
                self.add_installed_mod(mod_path)
            except NotAModPath:
                pass
            except Exception:
                traceback.print_exc()

        pre_size = len(self.dict)
        self.dict = {
            name: m for name, m in self.dict.items() if name in self.by_name_version
        }
        if len(self.dict) != pre_size:
            self.modified = True

    def exit(self) -> None:
        if self.modified:
            data = {"mods": [m for m in self.dict.values()]}
            with open(self.MOD_LIST_FILE, "w", encoding="utf8") as fp:
                json.dump(data, fp, ensure_ascii=False, indent=2)

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

    def find_dep(self, dep: Dependency):
        if dep.type == DependencyType.CONFLICT:
            return True
        if dep.name not in self.by_name_version:
            return False
        vers = self.by_name_version[dep.name]
        ops = [ver for ver in vers.keys() if dep.meets(ver)]
        if ops:
            return vers[max(ops)]
        return False

    def check_dep(self, dep: Dependency, do_optional=False):
        if dep.type == DependencyType.CONFLICT:
            if dep.name in self.dict:
                return not self.dict[dep.name]["enabled"]
            return True
        if dep.name in self.dict:
            current = self.dict[dep.name]
            if "version" in current:
                current_ver = ModVersion(current["version"])
            else:
                current_ver = max(self.by_name_version[dep.name])
            return dep.meets(current_ver)
        if dep.type == "(?)" or (dep.type == "?" and not do_optional):
            return True
        return False

    def force_dep(self, dep: Dependency, do_optional=False):
        if dep.type == "!":
            if dep.name in self.dict:
                self.dict[dep.name]["enabled"] = False
            return True
        if dep.name in self.dict:
            current = self.dict[dep.name]
            if "version" in current:
                current_ver = ModVersion(current["version"])
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

    def install_mod(self, dep: Dependency):
        with opener.open(f"{_mod_portal}/api/mods/{dep.name}") as fp:
            info: PortalResult = json.load(fp)
        best_version = MIN_MOD_VERSION
        release = None
        for r in info["releases"]:
            v = ModVersion(r["version"])
            if not dep.meets(v):
                continue
            if v > best_version:
                best_version = v
                release = r
        if release is None:
            raise ValueError(f"No mods on portal matching dependency:{dep}")
        return self.download_mod(release)

    def download_mod(self, release: Release):
        cred = get_credentials()
        url = _mod_portal + release["download_url"] + "?" + parse.urlencode(cred)
        new_path = MODS.joinpath(release["file_name"])
        download(url, new_path)
        return self.add_installed_mod(new_path)

    def add_installed_mod(self, mod_path: dual_path):
        m = InstalledMod(mod_path)
        self.by_name_version[m.name][m.version] = m  # TODO: check duplicates?
        if m.name not in self.dict and m.name != "core":
            self.dict[m.name] = {"name": m.name, "enabled": self.new_enabled}
            self.modified = True
        return m

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
        m = PortalMod(release)
        self.by_name_version[m.name][m.version] = m

    def expand_dependencies(self, deps: set[Dependency]):
        collected: set[Dependency] = set()
        progress = True
        connection_issues = False
        while progress:
            expanding = deps
            deps = set()
            progress = False
            while expanding:
                dep = expanding.pop()
                if dep.type <= DependencyType.OPTIONAL:
                    # since this is an optional dependency, we don't need to expand it
                    progress = True
                    collected.add(dep)
                    continue
                m = self.find_dep(dep)
                if m is False:
                    deps.add(dep)
                    continue
                assert isinstance(m, Mod), f"Expected mod, got {type(m)}"
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

    def get_mod_path_parts(self, path: dual_path):
        if isinstance(path, Path):
            try:
                return path.relative_to(MODS).parts
            except:
                pass
            return path.relative_to(READ_DIR).parts
        parts = []
        while isinstance(path.parent, zPath):
            parts.append(path.name)
            path = path.parent
        return tuple(parts[::-1])

    def _iterate_over_all_mod_paths(self) -> Iterator[Path]:
        for folders_with_mods in [READ_DIR, MODS]:
            yield from folders_with_mods.iterdir()

    def iter_mods(
        self, require_enabled=True, mod_filter: re.Pattern | None = None
    ) -> Iterator[InstalledMod]:
        for m in self.dict.values():
            if m["enabled"] or not require_enabled:
                name = m["name"]
                if mod_filter and not mod_filter.fullmatch(name):
                    continue
                versions = self.by_name_version.get(name, {})
                if "version" in m:
                    ver = ModVersion(m["version"])
                    mod = versions.get(ver)
                    if isinstance(mod, InstalledMod):
                        yield mod
                        continue
                    raise ValueError(
                        f"Mod {name} version {ver} is not installed, but is in the mod list"
                    )
                for ver in sorted(versions, reverse=True):
                    mod = versions[ver]
                    if isinstance(mod, InstalledMod):
                        yield mod
                        break
                else:
                    raise ValueError(
                        f"Mod {name} is not installed, but is in the mod list"
                    )

    def iter_mod_files(
        self,
        inner_re_path: str,
        require_enabled=True,
        mod_filter: re.Pattern | None = None,
    ) -> Iterator[dual_path]:
        parts = inner_re_path.split("/")
        parts = [
            part if not self.fancy.search(part) else re.compile(part) for part in parts
        ]
        for mod in self.iter_mods(require_enabled, mod_filter):
            yield from mod.iterate_mods_files(parts)


class __mod_manger_factory(object):
    def __init__(self) -> None:
        self.mod_manager: ModManager | None = None

    def __enter__(self) -> ModManager:
        assert (
            self.mod_manager is None
        ), "Asking for a second mod manager before the first one is closed"
        self.mod_manager = ModManager()
        return self.mod_manager

    def __exit__(self, *args) -> None:
        assert isinstance(
            self.mod_manager, ModManager
        ), "Exiting mod manager without entering it first"
        self.mod_manager.exit()
        self.mod_manager = None


mods = __mod_manger_factory()


if __name__ == "__main__":
    print(Dependency.from_str("! stop >= 3.4.5").meets(ModVersion("3.4.5")))
    with mods as mod_manager:
        for mod in mod_manager.iter_mods():
            print(mod.name, mod.version)
        pass
