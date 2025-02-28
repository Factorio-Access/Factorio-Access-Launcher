import json
import os
from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Any, Iterable

from fa_paths import SCRIPT_OUTPUT, MODS
from launch_and_monitor import launch_with_params

CACHE = MODS.joinpath("cached_raw_sub.json")
MOD_INFO = MODS.joinpath("mod-list.json")
MOD_SETTINGS = MODS.joinpath("mod-settings.dat")

cached_fields = {
    "noise-expression": {
        "*": {
            "type": True,
            "name": True,
            "intended_property": True,
            "order": False,
            "localised_name": False,
            "localised_description": False,
        }
    },
    "map-gen-presets": True,
    "autoplace-control": True,
}


class MissingData(ValueError):
    pass


@dataclass(kw_only=True)
class PrototypeBase:
    type: str
    name: str
    order: str = ""
    localised_name: Any = None
    localised_description: Any = None
    factoriopedia_description: Any = None
    subgroup: str | None = None
    hidden: bool = False
    hidden_in_factoriopedia: bool = False
    parameter: bool = False
    factoriopedia_simulation: Any = None


@dataclass(kw_only=True)
class Prototype(PrototypeBase):
    factoriopedia_alternative = None


class autoplace_category(StrEnum):
    resource = auto()
    terrain = auto()
    cliff = auto()
    enemy = auto()

    def __post_init__(self):
        if not self.localised_name:
            self.localised_name = ("gui-map-generator." + self.name,)
        if not self.localised_description:
            self.localised_description = (
                "?",
                "gui-map-generator." + self.name + "-description",
            )


@dataclass(kw_only=True)
class AutoplaceControl(Prototype):
    category: autoplace_category
    richness: bool = False
    can_be_disabled: bool = True


@dataclass(kw_only=True)
class NamedNoiseExpression(Prototype):
    intended_property: str = ""


# copies by reference
def extract_fields(template, data):
    if template is True or template is False:
        return data
    ret = {}
    for name, sub_template in template.items():
        if name == "*":
            for data_name, sub_data in data.items():
                try:
                    ret[data_name] = extract_fields(sub_template, sub_data)
                except MissingData:
                    pass
        else:
            if name in data:
                ret[name] = extract_fields(sub_template, data[name])
            elif sub_template:
                raise MissingData()
    return ret


def refresh_file_data():
    out_path = SCRIPT_OUTPUT.joinpath("data-raw-dump.json")
    out_path.unlink(missing_ok=True)
    launch_with_params(["--dump-data"], save_rename=False)
    with out_path.open(encoding="utf8") as fp:
        full_data = json.load(fp)
    selected_data = extract_fields(cached_fields, full_data)
    with CACHE.open("w", encoding="utf8") as fp:
        json.dump(selected_data, fp)
    return selected_data


def from_cache():
    try:
        with CACHE.open(encoding="utf8") as fp:
            return json.load(fp)
    except FileNotFoundError:
        return refresh_file_data()


local_cache = {}
local_cache_time = 0


def get_prototype_data():
    global local_cache
    global local_cache_time
    by_time = max([os.path.getmtime(p) for p in [MOD_INFO, MOD_SETTINGS]])
    if local_cache_time >= by_time:
        return local_cache
    local_cache = None
    try:
        if os.path.getmtime(CACHE) >= by_time:
            local_cache = from_cache()
    except FileNotFoundError:
        pass
    if not local_cache:
        local_cache = refresh_file_data()
    local_cache_time = by_time
    return local_cache


def autoplace_controls(cat: autoplace_category):
    data = get_prototype_data()
    specs: list[AutoplaceControl] = []
    for spec_dict in data["autoplace-control"].values():
        spec = AutoplaceControl(**spec_dict)
        if spec.category == cat:
            specs.append(spec)
    specs.sort(key=lambda spec: spec.order)
    return specs


if __name__ == "__main__":
    data = get_prototype_data()
    print(json.dumps(data, indent=3))
    for n, p in data["autoplace-control"].items():
        temp = AutoplaceControl(**p)
        print(temp)
    for n, p in data["noise-expression"].items():
        temp = NamedNoiseExpression(**p)
        print(temp)
