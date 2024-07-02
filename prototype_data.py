import json
import os
from fa_paths import SCRIPT_OUTPUT, MODS
from launch_and_monitor import launch_with_params

CACHE = MODS.joinpath("cached_raw_sub.json")
MOD_INFO = MODS.joinpath("mod-list.json")
MOD_SETTINGS = MODS.joinpath("mod-settings.dat")

cached_fields = {
    "noise-expression": {"*": {"intended_property": True}},
    "map-gen-presets": True,
    "autoplace-control": True,
}


# copies by reference
def extract_fields(template, data):
    if template is True:
        return data
    ret = {}
    for name, sub_template in template.items():
        if name == "*":
            for data_name, sub_data in data.items():
                ret[data_name] = extract_fields(sub_template, sub_data)
        else:
            ret[name] = extract_fields(sub_template, data[name])
    return ret


def refresh_file_data():
    launch_with_params(["--dump-data"], save_rename=False)
    with SCRIPT_OUTPUT.joinpath("data-raw-dump.json").open(encoding="utf8") as fp:
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
