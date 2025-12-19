import json
import os
from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import Any, Iterable
from collections import defaultdict
from copy import deepcopy

from fa_paths import SCRIPT_OUTPUT, MODS
from launch_and_monitor import launch_with_params

CACHE = lambda: MODS() / "cached_raw_sub.json"
MOD_INFO = lambda: MODS() / "mod-list.json"
MOD_SETTINGS = lambda: MODS() / "mod-settings.dat"

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
    "planet": {
        "*": {
            "name": True,
            "map_gen_settings": {
                "cliff_settings": True,
                "autoplace_controls": True,
                "moisture_climate_control": False,
                "aux_climate_control": False,
            },
            "order": False,
            "localised_name": False,
            "localised_description": False,
        },
    },
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


@dataclass(kw_only=True)
class AutoplaceControl(Prototype):
    category: autoplace_category
    richness: bool = False
    can_be_disabled: bool = True
    related_to_fight_achievements: bool = False
    planets: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.localised_name:
            self.localised_name = ("autoplace-control-names." + self.name,)
        if not self.localised_description:
            self.localised_description = (
                "?",
                "gui-map-generator." + self.name + "-description",
            )


@dataclass(kw_only=True)
class NamedNoiseExpression(Prototype):
    intended_property: str = ""

    def __post_init__(self):
        if not self.localised_name:
            self.localised_name = ("noise-expression." + self.name,)
        if not self.localised_description:
            self.localised_description = (
                "?",
                "gui-map-generator." + self.name + "-description",
            )


@dataclass(kw_only=True)
class MapGenSettings(PrototypeBase):
    pass


@dataclass(kw_only=True)
class AdvancedMapGenSettings(PrototypeBase):
    pass


@dataclass(kw_only=True)
class MapGenPreset:
    name: str
    order: str
    default: bool = False
    overlay: dict


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
    out_path = SCRIPT_OUTPUT().joinpath("data-raw-dump.json")
    out_path.unlink(missing_ok=True)
    launch_with_params(["--dump-data"], save_rename=False)
    with out_path.open(encoding="utf8") as fp:
        full_data = json.load(fp)
    selected_data = extract_fields(cached_fields, full_data)
    with CACHE().open("w", encoding="utf8") as fp:
        json.dump(selected_data, fp, indent=2)
    return selected_data


def from_cache():
    try:
        with CACHE().open(encoding="utf8") as fp:
            return json.load(fp)
    except FileNotFoundError:
        return refresh_file_data()


local_cache = {}
local_cache_time = 0


def get_prototype_data():
    global local_cache
    global local_cache_time
    by_time = 0
    for p in [MOD_INFO, MOD_SETTINGS]:
        try:
            p_time = p().stat().st_mtime
        except FileNotFoundError:
            continue
        if p_time > by_time:
            by_time = p_time
    if local_cache_time >= by_time:
        return local_cache
    local_cache = None
    try:
        if CACHE().stat().st_mtime >= by_time:
            local_cache = from_cache()
    except FileNotFoundError:
        pass
    if not local_cache:
        local_cache = refresh_file_data()
    local_cache_time = by_time
    return local_cache


def order_key_dict(d: dict):
    return d["order"]


def order_key(p: PrototypeBase):
    return p.order


def autoplace_controls(cat: autoplace_category):
    data = get_prototype_data()
    planets_per_autoplace = defaultdict(list)
    for planet in sorted(data["planet"].values(), key=order_key_dict):
        for control in planet["map_gen_settings"]["autoplace_controls"].keys():
            planets_per_autoplace[control].append(planet["name"])

    specs: list[AutoplaceControl] = []
    for spec_dict in data["autoplace-control"].values():
        spec = AutoplaceControl(**spec_dict)
        spec.planets = planets_per_autoplace[spec.name]
        if spec.category == cat:
            specs.append(spec)
    specs.sort(key=order_key)
    return specs


def get_planets_for(control: str):
    return (
        planet["name"]
        for planet in sorted(
            get_prototype_data()["planet"].values(), key=order_key_dict
        )
        if planet["map_gen_settings"].get(f"{control}_climate_control", False)
    )


def dropdown_expressions() -> dict[str, list[NamedNoiseExpression]]:
    data = get_prototype_data()
    dropdowns = defaultdict(list[NamedNoiseExpression])
    for exp in data["noise-expression"].values():
        expr = NamedNoiseExpression(**exp)
        dropdowns[expr.intended_property].append(expr)
    filtered = {}
    for property, expressions in dropdowns.items():
        if len(expressions) < 2:
            continue
        filtered[property] = sorted(expressions, key=order_key)
    return filtered


def get_presets() -> list[MapGenPreset]:
    raw_presets = get_prototype_data()["map-gen-presets"]["default"]
    presets = []
    for name, augmented_overlay in raw_presets.items():
        if name in ["type", "name"]:
            continue
        order = augmented_overlay.get("order", "")
        default = augmented_overlay.get("default", False)
        overlay = {}
        for sub_name in ["basic_settings", "advanced_settings"]:
            if sub_name in augmented_overlay:
                overlay[sub_name] = deepcopy(augmented_overlay[sub_name])
        presets.append(
            MapGenPreset(name=name, order=order, default=default, overlay=overlay)
        )
    presets.sort(key=order_key)
    return presets


if __name__ == "__main__":
    for cat in autoplace_category:
        for c in autoplace_controls(cat):
            pass
            # print(c)
    data = get_prototype_data()
    for n, p in data["noise-expression"].items():
        temp = NamedNoiseExpression(**p)
        # print(temp)
    # print(get_presets())
    print(dropdown_expressions())
