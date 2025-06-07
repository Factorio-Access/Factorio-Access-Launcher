import re
from collections import defaultdict
from typing import NamedTuple
import json

import fa_paths
import translations
from launch_and_monitor import launch_with_params
from mods import mod_manager


class Scenario(NamedTuple):
    order: str
    start_key: str
    name: translations.localised_str
    description: translations.localised_str


def get_scenario_from_path(path):
    with path.open(encoding="utf8") as fp:
        json_desc = json.load(fp)
    parts = mod_manager.get_mod_path_parts(path)
    key = parts[0] + "/" + parts[2]
    locale = path.parent.joinpath("locale")
    if not locale:
        return None
    temp_translations = defaultdict(dict)
    for code in ["en", translations.code]:
        sub = locale.joinpath(code)
        if not sub.is_dir():
            continue
        for possible_cfg in sub.iterdir():
            if not possible_cfg.name.endswith(".cfg"):
                continue
            with open(possible_cfg, encoding="utf8") as fp:
                translations.read_cfg(fp, ret=temp_translations)
    return Scenario(
        json_desc["order"],
        key,
        temp_translations[""]["scenario-name"],
        temp_translations[""]["description"],
    )


def get_freeplay():
    return get_scenario_from_path(
        fa_paths.READ_DIR.joinpath("base", "scenarios", "freeplay", "description.json")
    )


def get_scenarios(m_scenario=None):
    if m_scenario:
        return m_scenario.name
    scenarios = []
    with mod_manager:
        for path in mod_manager.iter_mod_files(
            "scenarios/.*/description.json", True, re.compile(r"FactorioAccess.*")
        ):
            scenario = get_scenario_from_path(path)
            if scenario:
                scenarios.append(scenario)
    scenarios.sort()
    return [(s.name, s) for s in scenarios]


def launch_scenario(scenario: Scenario):
    return launch_with_params(
        ["--load-scenario", scenario.start_key],
    )


def scenario_name(preset, *args):
    return preset.name


def scenario_desc(preset, *args):
    return preset.description


pre_launch_scenario = {
    get_scenarios: {"_desc": scenario_desc, ("gui-new-game.play",): launch_scenario},
}

if __name__ == "__main__":
    print(get_scenarios())
