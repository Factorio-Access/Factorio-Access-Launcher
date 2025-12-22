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
from credentials import get_credentials
from factorio_web import get_json, quote, download

_mod_portal = "https://mods.factorio.com"

dual_path = zPath | Path


class NotAModPath(ValueError):
    pass


class UnresolvedModDependency(Exception):
    pass


class FactorioVersionMismatch(Exception):
    pass


class ModNotInstalled(Exception):
    pass


class PortalInfoJson(TypedDict):
    factorio_version: str
    dependencies: NotRequired[list[str]]


class ModInfoJson(PortalInfoJson):
    name: str
    version: str


class Release(TypedDict):
    download_url: str  # 	Path to download for a mod. starts with "/download" and does not include a full url. See #Downloading Mods
    file_name: str  # 	The file name of the release. Always seems to follow the pattern "{name}_{version}.zip"
    info_json: PortalInfoJson  # A copy of the mod's info.json file, only contains factorio_version in short version, also contains an array of dependencies in full version
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

    def __str__(self):
        return f'{"=" if self.epsilon == 0 else ""} {self.ver}'


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
                case ">":
                    min = VerComp(ver, 1)
                case ">=":
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
        if new_min > new_max:
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

    def __str__(self):
        prefix = f"{self.type} {self.name}".strip()
        if self.min == self.max:
            return f"{prefix} = {self.min.ver}"
        if VerComp(MIN_MOD_VERSION, 0) < self.max < VerComp(MAX_MOD_VERSION, 0):
            if self.min == VerComp(MIN_MOD_VERSION, 0):
                return f"{prefix} <{self.max}"
            return f"{prefix} >{self.min},{prefix} <{self.max}"
        if self.min == VerComp(MIN_MOD_VERSION, 0):
            return prefix
        return f"{prefix} >{self.min}"

    def __repr__(self) -> str:
        my_str = str(self)
        if "," in my_str:
            return f"Dependency({repr(str(self.type))}, {repr(self.name)}, {self.min}, {self.max})"
        return f"Dependency.from_str({repr(my_str)})"


class Dependencies(dict[str, Dependency]):
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
    info: ModInfoJson

    def __init__(self, info: ModInfoJson) -> None:
        self.info = info
        if "dependencies" in info:
            self.dependencies = Dependencies(info["dependencies"])
        else:
            self.dependencies = None
        self.version = ModVersion(info["version"])
        self.name = info["name"]


class InstalledMod(Mod):
    dependencies: Dependencies

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
            i: ModInfoJson = json.load(fp)
        if path.name == "core":
            i["version"] = FACTORIO_VERSION()
        if path.parent == READ_DIR():
            i["factorio_version"] = factorio_version
        re_name = f"{i['name']}(_{i['version']}(.zip)?)?"
        if not re.fullmatch(re_name, path.name):
            raise ValueError(
                f"""Mod path mismatch:
   mod path: {path}
   name:{path.name}
   re:{re_name}"""
            )
        if "dependencies" not in i:
            i["dependencies"] = ["base"]
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
        if isinstance(part, re.Pattern):
            subs = (sub for sub in path.iterdir() if part.fullmatch(sub.name))
        else:
            subs = iter([path / part])
        for sub in subs:
            yield from InstalledMod._iter_files_sub(parts[1:], sub)

    def iterate_mods_files(self, parts: list[Union[str, re.Pattern]]):
        yield from self._iter_files_sub(parts, self.folder_path)


class PortalMod(Mod):
    def __init__(self, release: Release, name) -> None:
        info: ModInfoJson = {
            "factorio_version": release["info_json"]["factorio_version"],
            "name": name,
            "version": release["version"],
        }
        if "dependencies" in release["info_json"]:
            info["dependencies"] = release["info_json"]["dependencies"]
        super().__init__(info)
        self.release = release


class DepCheckResult(StrEnum):
    OK = "OK"
    ENABLE = "ENABLE"
    DISABLE = "DISABLE"
    INSTALL = "INSTALL"
    VERSION_SWITCH = "VERSION_SWITCH"


DepCheckResults = dict[DepCheckResult, set[Dependency]]


class ModManager(object):
    _re_factorio_ver = re.compile(r"\d+\.\d+")

    def __init__(self) -> None:
        global factorio_version
        factorio_version = self._re_factorio_ver.search(FACTORIO_VERSION())[0]
        self.mod_list_file = MODS() / "mod-list.json"
        with config.current_conf as conf:
            self.new_enabled = conf.other.enable_new_mods == "true"
        try:
            with open(self.mod_list_file, "r", encoding="utf8") as fp:
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
            except FactorioVersionMismatch:
                pass

        pre_size = len(self.dict)
        self.dict = {
            name: m for name, m in self.dict.items() if name in self.by_name_version
        }
        if len(self.dict) != pre_size:
            self.modified = True

    def exit(self) -> None:
        if self.modified:
            data = {"mods": [m for m in self.dict.values()]}
            with open(self.mod_list_file, "w", encoding="utf8") as fp:
                json.dump(data, fp, ensure_ascii=False, indent=2)

    def enabled(self) -> list[str]:
        return [name for name, m in self.dict.items() if m["enabled"]]

    def set_enabled(self, name: str, val: bool) -> None:
        self.dict[name]["enabled"] = val
        self.modified = True

    def enable(self, name) -> None:
        self.set_enabled(name, True)

    def disable(self, name) -> None:
        self.set_enabled(name, False)

    def select_version(self, name, version: ModVersion) -> None:
        self.dict[name]["version"] = str(version)
        self.modified = True

    def get_version(self, name: str):
        if name not in self.dict:
            raise ModNotInstalled(name)
        current = self.dict[name]
        if "version" in current:
            return ModVersion(current["version"])
        versions = self.by_name_version[name]
        for ver in sorted(versions, reverse=True):
            if isinstance(versions[ver], InstalledMod):
                return ver
        raise ModNotInstalled(name)

    def get_current_mod(self, name: str):
        ver = self.get_version(name)
        mod = self.by_name_version[name][ver]
        assert isinstance(mod, InstalledMod)
        return mod

    def get_current_mod_path(self, name: str):
        mod = self.get_current_mod(name)
        return mod.folder_path

    def find_dep(self, dep: Dependency, installed_only=False) -> Mod | None:
        assert dep.type != DependencyType.CONFLICT
        if dep.name not in self.by_name_version:
            return None
        vers = self.by_name_version[dep.name]
        for ver in sorted(vers, reverse=True):
            if not dep.meets(ver):
                continue
            mod = vers[ver]
            if installed_only and not isinstance(mod, InstalledMod):
                continue
            return mod
        return None

    def dep_from_mod(self, mod: Mod):
        return Dependency.from_str(f"{mod.name} = {mod.version}")

    def check_dep(
        self, dep: Dependency, req_optional=False
    ) -> tuple[DepCheckResult, Dependency]:
        if dep.type == DependencyType.CONFLICT:
            if dep.name in self.dict and self.dict[dep.name]["enabled"]:
                return (DepCheckResult.DISABLE, dep)
            return (DepCheckResult.OK, dep)
        req = (
            dep.type >= DependencyType.UNORDERED
            or dep.type == DependencyType.OPTIONAL
            and req_optional
        )
        try:
            current = self.get_version(dep.name)
        except ModNotInstalled:
            if not req:
                return (DepCheckResult.OK, dep)
        else:
            if dep.meets(current):
                return (DepCheckResult.OK, dep)
            good_version = self.find_dep(dep, installed_only=True)
            if good_version:
                dep = self.dep_from_mod(good_version)
                return (DepCheckResult.VERSION_SWITCH, dep)
        mod = self.find_dep(dep)
        if mod:
            dep = self.dep_from_mod(mod)
            return (DepCheckResult.INSTALL, dep)
        if req:
            raise UnresolvedModDependency(dep)
        return (DepCheckResult.DISABLE, Dependency.from_str(f"! {dep.name}"))

    def check_deps(self, deps: Dependencies, require_optional=False):
        ret: DepCheckResults = defaultdict(set)
        for dep in deps.values():
            res, dep = self.check_dep(dep, require_optional)
            ret[res].add(dep)
        return ret

    def exec_dep_check_res(self, res: DepCheckResults):
        for dep in res[DepCheckResult.ENABLE]:
            self.enable(dep.name)
        for dep in res[DepCheckResult.DISABLE]:
            self.disable(dep.name)
        for dep in res[DepCheckResult.VERSION_SWITCH]:
            self.select_version(dep.name, dep.min.ver)
        for dep in res[DepCheckResult.INSTALL]:
            self.install_mod(dep)

    def install_mod(self, dep: Dependency):
        mod = self.find_dep(dep)
        if isinstance(mod, InstalledMod):
            return mod
        if not mod:
            self.add_info_for_mods([dep.name])
        mod = self.find_dep(dep)
        if not mod:
            raise UnresolvedModDependency(dep)
        assert isinstance(mod, PortalMod)
        return self.download_mod(mod.release)

    def download_mod(self, release: Release):
        cred = get_credentials()
        url = _mod_portal + release["download_url"] + "?" + parse.urlencode(cred)
        new_path = MODS() / release["file_name"]
        download(url, new_path)
        return self.add_installed_mod(new_path)

    def add_installed_mod(self, mod_path: dual_path):
        m = InstalledMod(mod_path)
        if m.info.get("factorio_version") != factorio_version:
            raise FactorioVersionMismatch(m)
        self.by_name_version[m.name][m.version] = m  # TODO: check duplicates?
        if m.name not in self.dict and m.name != "core":
            self.dict[m.name] = {"name": m.name, "enabled": self.new_enabled}
            self.modified = True
        return m

    def add_dep_info_for_mod(self, mod_name: str):
        all_data: PortalResult = get_json(
            f"{_mod_portal}/api/mods/{quote(mod_name)}/full"
        )
        self.add_info_for_mod(all_data)

    def add_info_for_mods(self, mod_names: Iterable[str]):
        args = {
            "namelist": ",".join(mod_names),
        }
        info: PortalListResult = get_json(f"{_mod_portal}/api/mods", args)
        for r in info["results"]:
            self.add_info_for_mod(r)

    def add_dep_info_for_mods(self, mod_names: Iterable[str]):
        for name in mod_names:
            self.add_dep_info_for_mod(name)

    def add_info_for_mod(self, result: PortalResult):
        for release in result["releases"]:
            if release["info_json"].get("factorio_version") == factorio_version:
                self.add_info_for_release(release, result["name"])

    def add_info_for_release(self, release: Release, name: str):
        m = PortalMod(release, name)
        to_replace = self.by_name_version[m.name].get(m.version)
        if isinstance(to_replace, InstalledMod):
            return
        self.by_name_version[m.name][m.version] = m

    def expand_dependencies(self, deps: Iterable[Dependency]):
        collected: set[Dependency] = set()
        progress = True
        connection_issues = False
        looked_up = set()
        while deps:
            expanding = set(deps)
            deps = set()
            while expanding:
                dep = expanding.pop()
                if not dep.type <= DependencyType.OPTIONAL:
                    # since this is not optional dependency, we need to expand it
                    m = self.find_dep(dep)
                    if not m or m.dependencies is None:
                        if dep in looked_up:
                            raise UnresolvedModDependency(dep)
                        deps.add(dep)
                        # we'll try to resolve this later after downloading the mod
                        continue
                    new_deps = set(m.dependencies.values())
                    new_deps -= collected
                    new_deps -= deps
                    expanding |= new_deps
                collected.add(dep)
            if not deps:
                break
            self.add_dep_info_for_mods(set((d.name for d in deps)))
            looked_up |= deps

        return Dependencies(collected)

    def get_updatable(self, require_enabled=True):
        """Check for updates to installed mods.
        Returns a set of dependencies listing latest updates available."""
        check = []
        for mod in self.iter_installed_mods(require_enabled=require_enabled):
            if mod.folder_path.parent == READ_DIR():  # don't check built in
                continue
            check.append(mod.name)
        self.add_info_for_mods(check)
        deps: set[Dependency] = set()
        for mod in self.iter_installed_mods(require_enabled=require_enabled):
            current_ver = mod.version
            versions = self.by_name_version[mod.name]
            ver = max(versions)
            if ver > current_ver:
                v = VerComp(ver, 0)
                deps.add(Dependency(DependencyType.NORMAL, mod.name, v, v))
        return deps

    def check_updates(self, require_enabled=True):
        deps = self.get_updatable(require_enabled)
        exp_deps = self.expand_dependencies(deps)
        return self.check_deps(exp_deps)

    fancy = re.compile(r"[*.?()\[\]]")

    def get_mod_path_parts(self, path: dual_path):
        if isinstance(path, Path):
            try:
                return path.relative_to(MODS()).parts
            except:
                pass
            return path.relative_to(READ_DIR()).parts
        parts = []
        while isinstance(path.parent, zPath):
            parts.append(path.name)
            path = path.parent
        return tuple(parts[::-1])

    def _iterate_over_all_mod_paths(self) -> Iterator[Path]:
        for folders_with_mods in [READ_DIR(), MODS()]:
            yield from folders_with_mods.iterdir()

    def iter_installed_mods(
        self, require_enabled=True, mod_filter: re.Pattern | None = None
    ) -> Iterator[InstalledMod]:
        for m in self.dict.values():
            if m["enabled"] or not require_enabled:
                name = m["name"]
                if mod_filter and not mod_filter.fullmatch(name):
                    continue
                yield self.get_current_mod(name)

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
        for mod in self.iter_installed_mods(require_enabled, mod_filter):
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
        for mod in mod_manager.iter_installed_mods():
            print(mod.name, mod.version)
        try:
            actions = mod_manager.check_updates()
        except IncompatibleDependencies as e:
            # todo: handle this better
            raise e
        for action in DepCheckResult:
            if action == DepCheckResult.OK:
                continue
            my_actions = actions[action]
            if not my_actions:
                continue
            print(action)
            for i in my_actions:
                print("    ", i)
        mod_manager.exec_dep_check_res(actions)
