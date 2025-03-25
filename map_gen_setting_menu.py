import json
from typing import Any, Callable
import weakref
from copy import deepcopy
import collections.abc

import fa_paths
import fa_menu
from translations import localised_str
from launch_and_monitor import launch_with_params, launch
import prototype_data

BASIC = "basic_settings"
ADVANCED = "advanced_settings"

AUTO = "autoplace_controls"

DEFAULT_DATA_PATHS = {
    BASIC: fa_paths.READ_DIR.joinpath("map-gen-settings.example.json"),
    ADVANCED: fa_paths.READ_DIR.joinpath("map-settings.example.json"),
}
FLAGS = {
    BASIC: "--map-gen-settings",
    ADVANCED: "--map-settings",
}
JSON_OUTPUT_PATHS = {
    BASIC: fa_paths.SCRIPT_OUTPUT.joinpath("map_gen.json"),
    ADVANCED: fa_paths.SCRIPT_OUTPUT.joinpath("map.json"),
}


def update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


class json_map_settings(object):
    def __init__(self):
        self.defaults = {}
        for name, path in DEFAULT_DATA_PATHS.items():
            with path.open(encoding="utf8") as fp:
                self.defaults[name] = json.load(fp)
        self.load_preset({})

    def load_preset(self, preset):
        self.preset = update(deepcopy(self.defaults), preset)
        self.current = deepcopy(self.preset)

    def get(self, key_path):
        item = self.current
        for key in key_path:
            item = item[key]
        return item

    def set(self, key_path, val):
        item = self.current
        for key in key_path:
            prev_item = item
            item = item[key]
        prev_item[key] = val

    def reset_to_preset(self):
        self.current = deepcopy(self.preset)

    def save(self):
        for k, v in self.current.items():
            with JSON_OUTPUT_PATHS[k].open("w", encoding="utf8") as fp:
                json.dump(v, fp, indent=2)


settings = json_map_settings()


class j_mix(object):
    def __init__(self, *args, path: tuple[str], settings=settings, **kwargs) -> None:
        self.settings = settings
        self.path = path[::-1]
        super().__init__(*args, **kwargs)

    def make_key(self, l_args: list):
        return tuple(l_args.pop(0).name if i == "_arg" else i for i in self.path)[::-1]

    def val_to_string(self, *args):
        l_args = list(args)
        k = self.make_key(l_args)
        self.val = self.settings.get(k)
        return super().val_to_string(*l_args)

    def set_val(self, val, *args):
        self.settings.set(self.make_key(list(args)), val)


class enable_disable_menu(fa_menu.Menu):
    def __init__(
        self,
        name: localised_str | Callable[..., Any] | dict,
        submenu: dict,
        desc: localised_str | None = None,
    ) -> None:
        self.enabler = enable_disable_submenu(self)
        rest = submenu
        if not isinstance(submenu, list):
            rest, _ = fa_menu.parse_menu_dict(submenu)
        super().__init__(name, [self.enabler] + rest, desc, True)
        self.full_submenu = self.items
        self.remake_submenu()

    def get_items(self, *args):
        return {("", self._title, ": ", self.enabler.val_to_string(*args)): ()}

    def got_toggled(self, *args):
        pass

    def remake_submenu(self):
        if self.enabler.val:
            self.items = self.full_submenu
        else:
            self.items = self.items[:2]

    def __call__(self, *args):
        self.remake_submenu()
        return super().__call__(*args)


class enable_disable_submenu(fa_menu.setting_menu_bool):
    def __init__(
        self,
        parent: enable_disable_menu,
        desc: localised_str | None = None,
        default=True,
        val=True,
    ) -> None:
        self.parent = weakref.ref(parent)
        super().__init__(("gui-map-generator.enabled",), desc, default, val)

    def __call__(self, *args):
        super().__call__(*args)
        self.parent().got_toggled(*args)
        self.parent().remake_submenu()
        return 0


class autoplace_enable_disable_menu(enable_disable_menu):
    """This is used because when an autoplace control is disabled
    the subitems are just set to zero."""

    def got_toggled(self, *args):
        if not self.enabler.val:
            for sub in self.full_submenu[2:]:
                sub.val = 0
        else:
            for sub in self.full_submenu[2:]:
                sub.val = sub.default
        return super().got_toggled(*args)

    def remake_submenu(self):
        # hack for refreshes
        self.enabler.val = self.full_submenu[-1].val != 0
        return super().remake_submenu()


class autoplace_menu(fa_menu.Menu_var):
    resource = prototype_data.autoplace_category.resource

    def __init__(
        self,
        autoplace_finder: Callable,
        submenu: list,
    ) -> None:
        self.enabler = enable_disable_submenu(self)
        super().__init__(autoplace_finder, [self.enabler] + submenu)
        self.full_submenu = self.items

    def get_title(self, spec: prototype_data.AutoplaceControl, *args):
        return spec.localised_name

    def refresh_items(self, spec: prototype_data.AutoplaceControl):
        start = 1
        if spec.can_be_disabled:
            start = 0
            if not self.enabler.val:
                self.items = [self.enabler]
                return
        end = len(self.full_submenu)
        if spec.type == self.resource and not spec.richness:
            end -= 1
        self.items = self.full_submenu[start:end]

    def got_toggled(self, spec: prototype_data.AutoplaceControl, *args):
        if not self.enabler.val:
            for sub in self.full_submenu[2:]:
                sub.val = 0
        else:
            for sub in self.full_submenu[2:]:
                sub.val = sub.default
        self.refresh_items(spec)
        return super().got_toggled(*args)

    def __call__(self, spec: prototype_data.AutoplaceControl, *args):
        self.refresh_items(spec)
        return super().__call__(spec, *args)


class menu_setting_inverse_float(fa_menu.setting_menu_float):
    def val_to_string(self, *args):
        if self.val == 0:
            self.val = 1.0
        return str(1.0 / self.val)

    def input_to_val(self, inp: str, *args):
        return 1.0 / float(inp)


class menu_setting_cliff_freq(fa_menu.setting_menu_float):
    def val_to_string(self, *args):
        if self.val == 0:
            self.val = 1.0
        return str(40.0 / self.val)

    def input_to_val(self, inp: str, *args):
        return 40.0 / float(inp)


class menu_setting_evo(fa_menu.setting_menu_float):
    def val_to_string(self, *args):
        return str(int(self.val * 1e7 + 0.5))

    def input_to_val(self, inp: str, *args):
        return float(inp) * 1e-7


class menu_setting_ticks_to_min(fa_menu.setting_menu_int):
    def val_to_string(self, *args):
        return f"{self.val/3600:.2f}"

    def input_to_val(self, inp: str, *args):
        return int(float(inp) * 3600)


class menu_seed(fa_menu.setting_menu_int):
    def val_to_string(self, *args):
        if self.val is None:
            return ("gui-map-generator.randomize-map-seed",)
        return f"{self.val}"

    def input_to_val(self, inp: str, *args):
        ret = None
        try:
            ret = int(inp)
        except:
            pass
        return ret


data = {}


def refresh_data():
    global data
    data_loc = fa_paths.SCRIPT_OUTPUT.joinpath("data-raw-dump.json")
    try:
        with data_loc.open(encoding="utf8") as fp:
            data = json.load(fp)
    except FileNotFoundError:
        launch_with_params(["--dump-data"], save_rename=False)
        with data_loc.open(encoding="utf8") as fp:
            data = json.load(fp)


refresh_data()


map_types = {}
for name, exp in data["noise-expression"].items():
    if "intended_property" in exp and exp["intended_property"] == "elevation":
        map_types[("noise-expression." + name,)] = name

mgs_json = {  # Map Gen Settings Json file
    "terrain_segmentation": menu_setting_inverse_float(
        ("gui-map-generator.scale",), ("gui-map-generator.terrain-scale-description",)
    ),
    "water": fa_menu.setting_menu_float(
        ("gui-map-generator.coverage",),
        ("gui-map-generator.terrain-coverage-description",),
    ),
    "width": fa_menu.setting_menu_int(("gui-map-generator.map-width",)),
    "height": fa_menu.setting_menu_int(("gui-map-generator.map-height",)),
    "starting_area": fa_menu.setting_menu_float(
        ("gui-map-generator.starting-area-size",),
        ("gui-map-generator.starting-area-size-description",),
    ),
    "peaceful_mode": fa_menu.setting_menu_bool(
        ("gui-map-generator.peaceful-mode-checkbox",),
        ("gui-map-generator.peaceful-mode-description",),
        False,
        False,
    ),
    "autoplace_controls": {},
    "cliff_settings": {
        "cliff_elevation_interval": menu_setting_cliff_freq(
            ("gui-map-generator.cliff-frequency",),
            ("gui-map-generator.cliff-frequency-description",),
            40,
            40,
        ),
        "richness": fa_menu.setting_menu_float(
            ("gui-map-generator.cliff-continuity",),
            ("gui-map-generator.cliff-continuity-description",),
        ),
    },
    "property_expression_names": {
        "elevation": fa_menu.setting_menu_options(
            ("gui-map-generator.map-type",), map_types
        ),
        "control-setting:moisture:frequency:multiplier": menu_setting_inverse_float(
            ("gui-map-generator.scale",),
            ("gui-map-generator.terrain-scale-description",),
        ),
        "control-setting:moisture:bias": fa_menu.setting_menu_float(
            ("gui-map-generator.bias",),
            ("gui-map-generator.terrain-bias-description",),
            0,
            0,
        ),
        "control-setting:aux:frequency:multiplier": menu_setting_inverse_float(
            ("gui-map-generator.scale",),
            ("gui-map-generator.terrain-scale-description",),
        ),
        "control-setting:aux:bias": fa_menu.setting_menu_float(
            ("gui-map-generator.bias",),
            ("gui-map-generator.terrain-bias-description",),
            0,
            0,
        ),
    },
    "seed": menu_seed(
        ("gui-map-generator.map-seed",), ("fa-l.map-seed-description",), None, None
    ),
}

msj = {  # Map Settings Json
    "difficulty_settings": {
        "recipe_difficulty": fa_menu.setting_menu_options(
            ("gui-map-generator.difficulty",),
            {
                ("recipe-difficulty.normal",): 0,
                ("recipe-difficulty.expensive",): 1,
            },
            None,
            0,
            0,
        ),
        "technology_difficulty": fa_menu.setting_menu_options(
            ("gui-map-generator.difficulty",),
            {
                ("technology-difficulty.normal",): 0,
                ("technology-difficulty.expensive",): 1,
            },
            None,
            0,
            0,
        ),
        "technology_price_multiplier": fa_menu.setting_menu_int(
            ("gui-map-generator.price-multiplier",), None, 1, 1
        ),
    },
    "pollution": {
        "enabled": None,  # placeholder
        "diffusion_ratio": fa_menu.setting_menu_float(
            ("gui-map-generator.pollution-diffusion-ratio",),
            ("gui-map-generator.pollution-diffusion-ratio-description",),
            0.02,
            0.02,
        ),
        "ageing": fa_menu.setting_menu_float(
            ("gui-map-generator.pollution-absorption-modifier",),
            ("gui-map-generator.pollution-absorption-modifier-description",),
        ),
        "min_pollution_to_damage_trees": fa_menu.setting_menu_int(
            ("gui-map-generator.minimum-pollution-to-damage-trees",),
            ("gui-map-generator.minimum-pollution-to-damage-trees-description",),
            60,
            60,
        ),
        "pollution_restored_per_tree_damage": fa_menu.setting_menu_int(
            ("gui-map-generator.pollution-absorbed-per-tree-damaged",),
            ("gui-map-generator.pollution-absorbed-per-tree-damaged-description",),
            10,
            10,
        ),
        "enemy_attack_pollution_consumption_modifier": fa_menu.setting_menu_float(
            ("gui-map-generator.enemy-attack-pollution-consumption-modifier",),
            (
                "gui-map-generator.enemy-attack-pollution-consumption-modifier-description",
            ),
        ),
        "min_to_diffuse": fa_menu.setting_menu_int("min_to_diffuse", None, 15, 15),
        "expected_max_per_chunk": fa_menu.setting_menu_int(
            "expected_max_per_chunk", None, 150, 150
        ),
        "min_to_show_per_chunk": fa_menu.setting_menu_int(
            "min_to_show_per_chunk", None, 50, 50
        ),
        "pollution_with_max_forest_damage": fa_menu.setting_menu_int(
            "pollution_with_max_forest_damage", None, 150, 150
        ),
        "pollution_per_tree_damage": fa_menu.setting_menu_int(
            "pollution_per_tree_damage", None, 50, 50
        ),
        "max_pollution_to_restore_trees": fa_menu.setting_menu_int(
            "max_pollution_to_restore_trees", None, 20, 20
        ),
    },
    "enemy_evolution": {
        "enabled": None,  # placeholder
        "time_factor": menu_setting_evo(
            ("gui-map-generator.evolution-time-factor",),
            ("gui-map-generator.evolution-time-factor-description",),
            0.000004,
            0.000004,
        ),
        "destroy_factor": menu_setting_evo(
            ("gui-map-generator.evolution-destroy-factor",),
            ("gui-map-generator.evolution-destroy-factor-description",),
            0.002,
            0.002,
        ),
        "pollution_factor": menu_setting_evo(
            ("gui-map-generator.evolution-pollution-factor",),
            ("gui-map-generator.evolution-pollution-factor-description",),
            0.0000009,
            0.0000009,
        ),
    },
    "enemy_expansion": {
        "enabled": None,  # placeholder
        "max_expansion_distance": fa_menu.setting_menu_int(
            ("gui-map-generator.enemy-expansion-maximum-expansion-distance",),
            (
                "gui-map-generator.enemy-expansion-maximum-expansion-distance-description",
            ),
            7,
            7,
        ),
        "settler_group_min_size": fa_menu.setting_menu_int(
            ("gui-map-generator.enemy-expansion-minimum-expansion-group-size",),
            (
                "gui-map-generator.enemy-expansion-minimum-expansion-group-size-description",
            ),
            5,
            5,
        ),
        "settler_group_max_size": fa_menu.setting_menu_int(
            ("gui-map-generator.enemy-expansion-maximum-expansion-group-size",),
            (
                "gui-map-generator.enemy-expansion-maximum-expansion-group-size-description",
            ),
            20,
            20,
        ),
        "min_expansion_cooldown": menu_setting_ticks_to_min(
            ("gui-map-generator.enemy-expansion-minimum-expansion-cooldown",),
            (
                "gui-map-generator.enemy-expansion-minimum-expansion-cooldown-description",
            ),
            14400,
            14400,
        ),
        "max_expansion_cooldown": menu_setting_ticks_to_min(
            ("gui-map-generator.enemy-expansion-maximum-expansion-cooldown",),
            (
                "gui-map-generator.enemy-expansion-maximum-expansion-cooldown-description",
            ),
            216000,
            216000,
        ),
        "min_base_spacing": 3,
        "friendly_base_influence_radius": 2,
        "enemy_building_influence_radius": 2,
        "building_coefficient": 0.1,
        "other_base_coefficient": 2.0,
        "neighbouring_chunk_coefficient": 0.5,
        "neighbouring_base_chunk_coefficient": 0.4,
        "max_colliding_tiles_coefficient": 0.9,
    },
    "steering": {
        "default": {
            "radius": 1.2,
            "separation_force": 0.005,
            "separation_factor": 1.2,
            "force_unit_fuzzy_goto_behavior": False,
        },
        "moving": {
            "radius": 3,
            "separation_force": 0.01,
            "separation_factor": 3,
            "force_unit_fuzzy_goto_behavior": False,
        },
    },
    "unit_group": {
        "min_group_gathering_time": 3600,
        "max_group_gathering_time": 36000,
        "max_wait_time_for_late_members": 7200,
        "max_group_radius": 30.0,
        "min_group_radius": 5.0,
        "max_member_speedup_when_behind": 1.4,
        "max_member_slowdown_when_ahead": 0.6,
        "max_group_slowdown_factor": 0.3,
        "max_group_member_fallback_factor": 3,
        "member_disown_distance": 10,
        "tick_tolerance_when_member_arrives": 60,
        "max_gathering_unit_groups": 30,
        "max_unit_group_size": 200,
    },
    "path_finder": {
        "fwd2bwd_ratio": 5,
        "goal_pressure_ratio": 2,
        "max_steps_worked_per_tick": 100,
        "max_work_done_per_tick": 8000,
        "use_path_cache": True,
        "short_cache_size": 5,
        "long_cache_size": 25,
        "short_cache_min_cacheable_distance": 10,
        "short_cache_min_algo_steps_to_cache": 50,
        "long_cache_min_cacheable_distance": 30,
        "cache_max_connect_to_cache_steps_multiplier": 100,
        "cache_accept_path_start_distance_ratio": 0.2,
        "cache_accept_path_end_distance_ratio": 0.15,
        "negative_cache_accept_path_start_distance_ratio": 0.3,
        "negative_cache_accept_path_end_distance_ratio": 0.3,
        "cache_path_start_distance_rating_multiplier": 10,
        "cache_path_end_distance_rating_multiplier": 20,
        "stale_enemy_with_same_destination_collision_penalty": 30,
        "ignore_moving_enemy_collision_distance": 5,
        "enemy_with_different_destination_collision_penalty": 30,
        "general_entity_collision_penalty": 10,
        "general_entity_subsequent_collision_penalty": 3,
        "extended_collision_penalty": 3,
        "max_clients_to_accept_any_new_request": 10,
        "max_clients_to_accept_short_new_request": 100,
        "direct_distance_to_consider_short_request": 100,
        "short_request_max_steps": 1000,
        "short_request_ratio": 0.5,
        "min_steps_to_check_path_find_termination": 2000,
        "start_to_goal_cost_multiplier_to_terminate_path_find": 500.0,
        "overload_levels": [0, 100, 500],
        "overload_multipliers": [2, 3, 4],
        "negative_path_cache_delay_interval": 20,
    },
    "max_failed_behavior_count": 3,
}

json_files = {"basic_settings": mgs_json, "advanced_settings": msj}


selected_preset = None


def get_presets(*args):
    global selected_preset
    presets = []
    for preset_group in data["map-gen-presets"].values():
        for name, preset in preset_group.items():
            if name == "type" or name == "name":
                continue
            t_name = ("map-gen-preset-name." + name,)
            if args and args[-1] == preset:
                return t_name
            preset["name"] = name
            presets.append(
                (preset["order"] if "order" in preset else "", t_name, preset)
            )
    presets.sort()
    if selected_preset is None:
        select_preset(presets[0][2])
    for i, p in enumerate(presets):
        if p[2] == selected_preset:
            t_name = p[1]
            if check_vals(p[2], json_files) > 0:
                add = ("gui-map-generator.custom",)
            else:
                add = ("fa-l.selected",)
            t_name = ("", t_name, add)
            presets[i] = (p[0], t_name, p[2])
    return {p[1]: (p[2],) for p in presets}


def select_preset(preset):
    global selected_preset
    selected_preset = preset
    set_vals(preset, json_files)
    return 0


def select_preset_name(preset):
    diffs = check_vals(preset, json_files)
    if diffs > 0:
        ret = ("gui-map-generator.reset-to-preset", diffs)
    else:
        ret = ("gui-map-generator.reset-to-preset-disabled",)
    return {ret: ()}


def get_preset_desc(*args):
    preset = args[-1]
    return ("map-gen-preset-description." + preset["name"],)


class SettingEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, fa_menu.Menu):
            return obj.val
        # Let the base class default method raise the TypeError
        return super().default(obj)


def launch_new_game_from_params(params):
    new_save = str(fa_paths.SAVES.joinpath("_autosave-new.zip").absolute())
    params += ["--create", new_save]
    launch_with_params(params, save_rename=False)
    return launch(new_save)


def launch_new_preset(preset, *args):
    p = preset["name"]
    return launch_new_game_from_params(["--preset", p])


def launch_new_custom(*args):
    mgs_path = fa_paths.SCRIPT_OUTPUT.joinpath("map_gen.json")
    ms_path = fa_paths.SCRIPT_OUTPUT.joinpath("map.json")
    files = {"basic_settings": mgs_path, "advanced_settings": ms_path}
    for sub, path in files.items():
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(
                json_files[sub], fp, ensure_ascii=False, indent=2, cls=SettingEncoder
            )
    return launch_new_game_from_params(
        ["--map-gen-settings", str(mgs_path), "--map-settings", str(ms_path)]
    )


menu = {
    select_preset_name: select_preset,
    "seed": mgs_json["seed"],
    ("gui-map-generator.resources-tab-title",): {},
    ("gui-map-generator.terrain-tab-title",): {
        "map_type": mgs_json["property_expression_names"]["elevation"],
        "Water": autoplace_enable_disable_menu(
            name=("gui-map-generator.water",),
            submenu={
                "Scale": mgs_json["terrain_segmentation"],
                "Coverage": mgs_json["water"],
            },
            desc=("size.only-starting-area",),
        ),
    },
    ("gui-map-generator.enemy-tab-title",): {},
    ("gui-map-generator.advanced-tab-title",): {
        "Record replay information": fa_menu.setting_menu_bool(
            title=("gui-map-generator.enable-replay",),
            desc=("gui-map-generator.enable-replay-description",),
            default=False,
            val=False,
        ),
        ("gui-map-generator.map-size-group-tile",): {
            "Width": mgs_json["width"],
            "Height": mgs_json["height"],
        },
        ("gui-map-generator.recipes-difficulty-group-tile",): {
            "Difficulty": msj["difficulty_settings"]["recipe_difficulty"],
        },
        ("gui-map-generator.technology-difficulty-group-tile",): {
            "Difficulty": msj["difficulty_settings"]["technology_difficulty"],
            "Price multiplier": msj["difficulty_settings"][
                "technology_price_multiplier"
            ],
        },
        ("gui-map-generator.pollution",): enable_disable_menu(
            ("gui-map-generator.pollution",),
            {
                "Absorption modifier": msj["pollution"]["ageing"],
                "Attack cost modifier": msj["pollution"][
                    "enemy_attack_pollution_consumption_modifier"
                ],
                "Minimum to damage trees": msj["pollution"][
                    "min_pollution_to_damage_trees"
                ],
                "Absorbed per damaged tree": msj["pollution"][
                    "pollution_restored_per_tree_damage"
                ],
                "Diffusion ratio": msj["pollution"]["diffusion_ratio"],
            },
        ),
    },
    ("gui-map-generator.play",): launch_new_custom,
}

msj["pollution"]["enabled"] = menu[("gui-map-generator.advanced-tab-title",)][
    ("gui-map-generator.pollution",)
].items[1]


for name, control in data["autoplace-control"].items():
    submenu = {}
    if "localised_name" not in control:
        control["localised_name"] = "autoplace-control-names." + control["name"]
    name = (control["localised_name"],)
    if control["category"] == "resource":
        parent = menu[("gui-map-generator.resources-tab-title",)]
        submenu["frequency"] = fa_menu.setting_menu_float(
            ("gui-map-generator.frequency",),
            ("gui-map-generator.resource-frequency-description",),
            1,
            1,
        )
        submenu["size"] = fa_menu.setting_menu_float(
            ("gui-map-generator.size",),
            ("gui-map-generator.resource-size-description",),
            1,
            1,
        )
        if "richness" in control and control["richness"]:
            submenu["richness"] = fa_menu.setting_menu_float(
                ("gui-map-generator.richness",),
                ("gui-map-generator.resource-richness-description",),
                1,
                1,
            )
        name = ("entity-name." + control["name"],)
    elif control["category"] == "terrain":
        parent = menu[("gui-map-generator.terrain-tab-title",)]
        submenu["frequency"] = menu_setting_inverse_float(
            ("gui-map-generator.scale",),
            ("gui-map-generator.terrain-scale-description",),
            1,
            1,
        )
        submenu["size"] = fa_menu.setting_menu_float(
            ("gui-map-generator.coverage",),
            ("gui-map-generator.terrain-coverage-description",),
            1,
            1,
        )
    else:
        parent = menu[("gui-map-generator.enemy-tab-title",)]
        submenu["frequency"] = fa_menu.setting_menu_float(
            ("gui-map-generator.frequency",),
            ("gui-map-generator.enemy-frequency-description",),
            1,
            1,
        )
        submenu["size"] = fa_menu.setting_menu_float(
            ("gui-map-generator.size",),
            ("gui-map-generator.enemy-size-description",),
            1,
            1,
        )

    if "can_be_disabled" not in control or control["can_be_disabled"]:
        my_menu = autoplace_enable_disable_menu(name, submenu)
    else:
        my_menu = fa_menu.Menu(name, *fa_menu.parse_menu_dict(submenu))
    parent[control["name"]] = my_menu
    mgs_json["autoplace_controls"][control["name"]] = submenu

menu[("gui-map-generator.terrain-tab-title",)].update(
    {
        "Cliffs": autoplace_enable_disable_menu(
            ("gui-map-generator.cliffs",),
            {
                "Frequency": mgs_json["cliff_settings"]["cliff_elevation_interval"],
                "Continuity": mgs_json["cliff_settings"]["richness"],
            },
        ),
        ("gui-map-generator.moisture",): {
            "_desc": ("gui-map-generator.moisture-description",),
            "Scale": mgs_json["property_expression_names"][
                "control-setting:moisture:frequency:multiplier"
            ],
            "Bias": mgs_json["property_expression_names"][
                "control-setting:moisture:bias"
            ],
        },
        ("gui-map-generator.aux",): {
            "_desc": ("gui-map-generator.aux-description",),
            "Scale": mgs_json["property_expression_names"][
                "control-setting:aux:frequency:multiplier"
            ],
            "Bias": mgs_json["property_expression_names"]["control-setting:aux:bias"],
        },
    }
)

menu[("gui-map-generator.enemy-tab-title",)].update(
    {
        "Peaceful mode": mgs_json["peaceful_mode"],
        "Starting area size": mgs_json["starting_area"],
        "Enemy Expansion": enable_disable_menu(
            ("gui-map-generator.enemy-expansion-group-tile",),
            {
                "Maximum expansion distance": msj["enemy_expansion"][
                    "max_expansion_distance"
                ],
                "Minimum group size": msj["enemy_expansion"]["settler_group_min_size"],
                "Maximum group size": msj["enemy_expansion"]["settler_group_max_size"],
                "Minimum cooldown": msj["enemy_expansion"]["min_expansion_cooldown"],
                "Maximum cooldown": msj["enemy_expansion"]["max_expansion_cooldown"],
            },
        ),
        "Evolution": enable_disable_menu(
            ("gui-map-generator.evolution",),
            {
                "Time factor": msj["enemy_evolution"]["time_factor"],
                "Destroy factor": msj["enemy_evolution"]["destroy_factor"],
                "Pollution factor": msj["enemy_evolution"]["pollution_factor"],
            },
        ),
    }
)

msj["enemy_expansion"]["enabled"] = menu[("gui-map-generator.enemy-tab-title",)][
    "Enemy Expansion"
].items[1]
msj["enemy_evolution"]["enabled"] = menu[("gui-map-generator.enemy-tab-title",)][
    "Evolution"
].items[1]


sub_preset = {
    get_presets: {
        "_desc": get_preset_desc,
        ("gui-map-generator.play",): launch_new_preset,
        ("fa-l.customize",): menu,
    },
}


def check_vals(preset, obj):
    diffs = 0
    for name, subobj in obj.items():
        have_preset = preset and name in preset
        if isinstance(subobj, dict):
            diffs += check_vals(preset[name] if have_preset else None, subobj)
            continue
        if not isinstance(subobj, fa_menu.setting_menu):
            continue
        if have_preset:
            check = preset[name]
        else:
            check = subobj.default
        if check != subobj.val:
            diffs += 1
    return diffs


def set_defaults(defs, obj):
    for name, subobj in obj.items():
        if name not in defs:
            continue
        if isinstance(subobj, dict):
            set_defaults(defs[name], subobj)
            continue
        if not isinstance(subobj, fa_menu.setting_menu):
            continue
        subobj.default = defs[name]


def set_vals(preset, obj):
    for name, subobj in obj.items():
        have_preset = preset and name in preset
        if isinstance(subobj, dict):
            set_vals(preset[name] if have_preset else None, subobj)
            continue
        if not isinstance(subobj, fa_menu.setting_menu):
            continue
        if have_preset:
            subobj.val = preset[name]
        else:
            subobj.val = subobj.default


class preset_menu(fa_menu.Menu):
    def __init__(self, triple_obj):
        self.t: dict = triple_obj
        submenu = []
        super().__init__(name, submenu, ("fa-l.map-setting-preset-description",), True)

    def populate(self, prototype_data):
        self.presets = []
        for preset_group in prototype_data["map-gen-presets"].values():
            for name, preset in preset_group.items():
                if name == "type" or name == "name":
                    continue
                order = preset["order"] if "order" in preset else ""
                t_name = ("map-gen-preset-name." + name,)
                preset["name"] = name
                self.presets.append((order, t_name, preset))
        self.presets.sort()
        if self.selected_preset is None:
            self.select_preset(self.presets[0][2])

    def select_preset(self, preset):
        self.t["preset"]


class map_settings_menu_gen(object):
    def __init__(self) -> None:
        self.presets = {}
        self.extra_terrain = {}
        self.resources = {}
        self.selected_preset: dict | None = None
        self.json_file_data = self.default_json_files()
        self.gen_menu_and_overwrite_json_file_data()

    def populate(self, prototype_data):
        self.populate_presets(prototype_data)

    def populate_presets(self, prototype_data):
        pass

    def get_preset_menu_list(self):
        ret = {}
        for p in self.presets:
            if p[2] == selected_preset:
                t_name = p[1]
                if self.check_vals(p[2], json_files) > 0:
                    add = ("gui-map-generator.custom",)
                else:
                    add = ("fa-l.selected",)
                t_name = ("", t_name, add)
                p = (p[0], t_name, p[2])
            ret[p[1]] = p[2]
        return ret

    def select_preset(self, preset):
        self.selected_preset = preset
        set_vals(preset, self.json_file_data)
        set_defaults(preset, self.json_file_data)
        return 0

    def default_json_files(self):
        data = fa_paths.READ_DIR.joinpath("data")
        regular = data.joinpath("map-settings.example.json")
        gen = data.joinpath("map-gen-settings.example.json")
        ret = {}
        with regular.open(encoding="utf8") as fp:
            ret["advanced_settings"] = json.load(fp)  # to match preset keys
        with gen.open(encoding="utf8") as fp:
            ret["basic_settings"] = json.load(fp)  # to match preset keys
        return ret


def tuple_localised_string(data):
    if isinstance(data, str):
        return data
    return tuple(tuple_localised_string(sub_data) for sub_data in data)


def get_autoplace(cat: prototype_data.autoplace_category):
    specs = prototype_data.autoplace_controls(cat)
    return {tuple_localised_string(spec.localised_name): (spec,) for spec in specs}


def get_resources():
    return get_autoplace(prototype_data.autoplace_category.resource)


class j_float(j_mix, fa_menu.setting_menu_float):
    pass


test_menu = {
    "expanded_resources": autoplace_menu(
        get_resources,
        [
            j_float(
                title=("gui-map-generator.frequency",),
                desc=("gui-map-generator.resource-frequency-description",),
                default=1,
                val=1,
                path=(BASIC, AUTO, "_arg", "frequency"),
            ),
            j_float(
                ("gui-map-generator.size",),
                ("gui-map-generator.resource-size-description",),
                1,
                1,
                path=(BASIC, AUTO, "_arg", "size"),
            ),
            j_float(
                ("gui-map-generator.richness",),
                ("gui-map-generator.resource-richness-description",),
                1,
                1,
                path=(BASIC, AUTO, "_arg", "richness"),
            ),
        ],
    )
}
