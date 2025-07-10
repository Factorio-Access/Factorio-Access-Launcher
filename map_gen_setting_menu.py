import json
from typing import Any, Callable, Protocol
import weakref
from copy import deepcopy
import collections.abc

import fa_paths
import fa_menu
from translations import localised_str, translate
from launch_and_monitor import launch_with_params, launch
import prototype_data

BASIC = "basic_settings"
ADVANCED = "advanced_settings"

AUTO = "autoplace_controls"
PROPERTY_EXPRESSION_NAMES = "property_expression_names"

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
    def __init__(self, preset: prototype_data.MapGenPreset):
        self.load_defaults()
        self.preset = update(deepcopy(self.defaults), preset.overlay)
        self.current = deepcopy(self.preset)

    def load_defaults(self):
        self.defaults = {}
        for name, path in DEFAULT_DATA_PATHS.items():
            with path.open(encoding="utf8") as fp:
                self.defaults[name] = json.load(fp)
        self.load_default_autoplace()
        self.load_default_property_expressions()

    def load_default_autoplace(self):
        autoplace = {}
        for c in prototype_data.autoplace_category:
            for a in prototype_data.autoplace_controls(c):
                default = {"frequency": 1, "size": 1}
                if a.richness:
                    default["richness"] = 1
                autoplace[a.name] = default
        self.defaults[BASIC][AUTO] = autoplace

    # https://lua-api.factorio.com/latest/concepts/PropertyExpressionNames.html
    def load_default_property_expressions(self):
        named: dict[str, str] = {  # hard coded first
            "control:moisture:frequency": "1",
            "control:moisture:bias": "0",
            "control:aux:frequency": "1",
            "control:aux:bias": "0",
        }
        for e in prototype_data.dropdown_expressions().keys():
            named[e] = e
        self.defaults[BASIC][PROPERTY_EXPRESSION_NAMES] = named

    @staticmethod
    def make_key(*args):
        l_args = list(args)
        path: tuple[str] = l_args.pop(0)
        key = tuple(l_args.pop(0).name if i == "_arg" else i for i in path)[::-1]
        self: __class__ = l_args.pop(0)
        return key, self

    @staticmethod
    def get(*args):
        key_path, self = __class__.make_key(*args)
        item = self.current
        for key in key_path:
            item = item[key]
        return item

    @staticmethod
    def set(val, *args):
        key_path, self = __class__.make_key(*args)
        item = self.current
        try:
            for key in key_path:
                prev_item = item
                item = item[key]
            prev_item[key] = val  # type: ignore error caught below
        except KeyError | UnboundLocalError:
            raise ValueError(
                "Either Factorio changed their json format or a dev messed up :("
            )

    def reset_to_preset(self):
        self.current = deepcopy(self.preset)

    def save(self):
        for k, v in self.current.items():
            with JSON_OUTPUT_PATHS[k].open("w", encoding="utf8") as fp:
                json.dump(v, fp, indent=2)


class set_preset_for_customize(fa_menu.Menu):
    def __call__(self, preset, *arg, **kwargs):
        settings = json_map_settings(preset)
        return super().__call__(settings, *arg, **kwargs)


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


class menu_seed(fa_menu.setting_menu):
    def val_to_string(self, *args):
        if self.val is None:
            return translate(("gui-map-generator.randomize-map-seed",))
        return f"{self.val}"

    def input_to_val(self, inp: str, *args):
        ret = None
        try:
            ret = int(inp)
        except:
            pass
        return ret


class enable_disable_menu(fa_menu.Menu):
    def __init__(
        self,
        title: fa_menu.Title,
        submenu: list[fa_menu.MenuBase],
        desc: fa_menu.DescFunc | localised_str | None = None,
        enabler: "enable_disable_submenu|None" = None,
    ):
        self.enabler = enabler if enabler is not None else enable_disable_submenu(self)
        submenu = [self.enabler] + submenu
        super().__init__(title, submenu, desc)
        self.full_submenu: list[fa_menu.setting_menu] = self.items

    def val_to_string(self, *args):
        return self.enabler.val_to_string(*args)

    def got_toggled(self, *args):
        self.remake_submenu(*args)

    def remake_submenu(self, *args):
        if self.enabler.val:
            self.items = self.full_submenu
        else:
            self.items = self.items[:2]

    def __call__(self, *args):
        self.remake_submenu(*args)
        return super().__call__(*args)


class enable_disable_submenu(fa_menu.setting_menu_bool):
    def __init__(
        self,
        parent: enable_disable_menu,
        desc: localised_str | None = None,
        default=None,
        val=None,
    ) -> None:
        self.parent = weakref.ref(parent)
        super().__init__(
            title=("gui-map-generator.enabled",),
            desc=desc,
            default=default,
            val=val,
        )

    def __call__(self, *args):
        super().__call__(*args)
        parent = self.parent()
        assert parent is not None
        parent.got_toggled(*args)
        return 0


class HasValToString(Protocol):
    def val_to_string(self, *args) -> str: ...


class j_mix(object):
    def __init__(self, *args, path: tuple[str, ...], **kwargs) -> None:
        self.path = path[::-1]
        super().__init__(*args, **kwargs)

    def val_to_string(self, *args):
        self.val = json_map_settings.get(self.path, *args)
        val_to_string: Callable[..., str] = getattr(super(), "val_to_string")
        assert callable(val_to_string)
        return val_to_string(*args)

    def set_val(self, val, *args):
        json_map_settings.set(val, self.path, *args)


class j_enable_disable_submenu(j_mix, enable_disable_submenu):
    pass


class j_float(j_mix, fa_menu.setting_menu_float):
    pass


class j_inv_float(j_mix, menu_setting_inverse_float):
    pass


class j_bool(j_mix, fa_menu.setting_menu_bool):
    pass


class j_seed(j_mix, menu_seed):
    pass


class autoplace_menu(enable_disable_menu):
    # for shorthand
    resource = prototype_data.autoplace_category.resource

    def get_title(self, *args):
        spec: prototype_data.AutoplaceControl = args[0]
        return spec.localised_name

    def remake_submenu(self, *args):
        spec: prototype_data.AutoplaceControl = args[0]
        start = 2
        if spec.can_be_disabled:
            check_sub = self.full_submenu[-1]
            check_sub.val_to_string(*args)  # hack to make sure it's up to date
            self.enabler.val = check_sub.val != 0
            start = 1
            if not self.enabler.val:
                self.items = self.full_submenu[0:2]
                return
        end = len(self.full_submenu)
        if spec.type == self.resource and not spec.richness:
            end -= 1
        self.items = self.full_submenu[:1] + self.full_submenu[start:end]

    def got_toggled(self, *args):
        spec: prototype_data.AutoplaceControl = args[0]
        self.enabler.val_to_string()  # hack to make sure val is up to date
        if self.enabler.val:
            for sub in self.full_submenu[2:]:
                sub.set_val(0, *args)
        else:
            for sub in self.full_submenu[2:]:
                sub.set_val(1, *args)
        return super().got_toggled(*args[1:])


class j_enable_disable_menu(enable_disable_menu):
    def __init__(
        self,
        name: fa_menu.Title,
        submenu: list[fa_menu.MenuBase],
        path,
        desc: fa_menu.DescFunc | localised_str | None = None,
    ) -> None:
        enabler = j_enable_disable_submenu(path=path, parent=self, desc=desc)
        super().__init__(name, submenu, desc, enabler)


_ = {
    "seed": j_seed(
        ("gui-map-generator.map-seed",),
        ("fa-l.map-seed-description",),
        path=(BASIC, "seed"),
    ),
}

pollution_subs: list[fa_menu.MenuBase] = [
    j_float(
        title=("gui-map-generator.pollution-absorption-modifier",),
        desc=("gui-map-generator.pollution-absorption-modifier-description",),
        path=(ADVANCED, "pollution", "ageing"),
    ),
    j_float(
        title=("gui-map-generator.enemy-attack-pollution-consumption-modifier",),
        desc=(
            "gui-map-generator.enemy-attack-pollution-consumption-modifier-description",
        ),
        path=(ADVANCED, "pollution", "enemy_attack_pollution_consumption_modifier"),
    ),
    j_float(
        title=("gui-map-generator.minimum-pollution-to-damage-trees",),
        desc=("gui-map-generator.minimum-pollution-to-damage-trees-description",),
        path=(ADVANCED, "pollution", "min_pollution_to_damage_trees"),
    ),
    j_float(
        title=("gui-map-generator.pollution-absorbed-per-tree-damaged",),
        desc=("gui-map-generator.pollution-absorbed-per-tree-damaged-description",),
        path=(ADVANCED, "pollution", "pollution_restored_per_tree_damage"),
    ),
    j_float(
        title=("gui-map-generator.pollution-diffusion-ratio",),
        desc=("gui-map-generator.pollution-diffusion-ratio-description",),
        path=(ADVANCED, "pollution", "diffusion_ratio"),
    ),
]

evolution_subs: list[fa_menu.MenuBase] = [
    j_float(
        title=(f"gui-map-generator.evolution-{kind}-factor",),
        desc=(f"gui-map-generator.evolution-{kind}-factor-description",),
        path=(ADVANCED, "enemy_evolution", kind + "_factor"),
    )
    for kind in ["time", "destroy", "pollution"]
]

expansion_subs: list[fa_menu.MenuBase] = [
    j_float(
        title=("gui-map-generator.enemy-expansion-maximum-expansion-distance",),
        desc=(
            "gui-map-generator.enemy-expansion-maximum-expansion-distance-description",
        ),
        path=(ADVANCED, "enemy_expansion", "max_expansion_distance"),
    ),
    j_float(
        title=("gui-map-generator.enemy-expansion-minimum-expansion-group-size",),
        desc=(
            "gui-map-generator.enemy-expansion-minimum-expansion-group-size-description",
        ),
        path=(ADVANCED, "enemy_expansion", "settler_group_min_size"),
    ),
    j_float(
        title=("gui-map-generator.enemy-expansion-maximum-expansion-group-size",),
        desc=(
            "gui-map-generator.enemy-expansion-maximum-expansion-group-size-description",
        ),
        path=(ADVANCED, "enemy_expansion", "settler_group_max_size"),
    ),
    j_float(
        title=("gui-map-generator.enemy-expansion-minimum-expansion-cooldown",),
        desc=(
            "gui-map-generator.enemy-expansion-minimum-expansion-cooldown-description",
        ),
        path=(ADVANCED, "enemy_expansion", "min_expansion_cooldown"),
    ),
    j_float(
        title=("gui-map-generator.enemy-expansion-maximum-expansion-cooldown",),
        desc=(
            "gui-map-generator.enemy-expansion-maximum-expansion-cooldown-description",
        ),
        path=(ADVANCED, "enemy_expansion", "max_expansion_cooldown"),
    ),
]


def get_presets(*args):
    return [
        (("map-gen-preset-name." + p.name,), p) for p in prototype_data.get_presets()
    ]


def get_preset_desc(preset, *args):
    return ("map-gen-preset-description." + preset.name,)


def launch_new_game_from_params(params):
    new_save = str(fa_paths.SAVES.joinpath("_autosave-new.zip").absolute())
    params += ["--create", new_save]
    launch_with_params(params, save_rename=False)
    return launch(new_save)


def launch_new_preset(preset, *args):
    p = preset.name
    return launch_new_game_from_params(["--preset", p])


def launch_new_custom(settings, *args):
    settings.save()
    params = []
    for t, f in FLAGS.items():
        params.append(f)
        params.append(str(JSON_OUTPUT_PATHS[t]))
    return launch_new_game_from_params(params)


class translate_dropdown(fa_menu.setting_menu_options):
    def val_to_string(self, *args):
        return translate(("noise-expression." + super().val_to_string(self, *args),))


class expanding_downdown_menu(j_mix, translate_dropdown):
    pass


class Dropdown(list[prototype_data.NamedNoiseExpression]):
    def __init__(self, *args, name: str, **kwargs):
        self.name = name
        super().__init__(*args, **kwargs)


def tuple_localised_string(data):
    if isinstance(data, str):
        return data
    return tuple(tuple_localised_string(sub_data) for sub_data in data)


def get_aux_desc(control: str, *args):
    desc = (f"gui-map-generator.{control}-description",)
    planet_list = ()
    for planet in prototype_data.get_planets_for(control):
        planet_list += ((f"space-location-name.{planet}",), ", ")
    if len(planet_list):
        desc = ("", desc, "\n", ("gui-map-generator.appears-on",), " ")
        desc += planet_list[:-1]
    return desc


def get_autoplace(cat: prototype_data.autoplace_category) -> fa_menu.ItemData:
    specs = prototype_data.autoplace_controls(cat)
    return [(spec.localised_name, spec) for spec in specs]


def get_resources(*args):
    return get_autoplace(prototype_data.autoplace_category.resource)


def get_terrain(*args):
    return get_autoplace(prototype_data.autoplace_category.terrain)


def get_cliffs(*args):
    return get_autoplace(prototype_data.autoplace_category.cliff)


def get_enemy(*args):
    return get_autoplace(prototype_data.autoplace_category.enemy)


def get_dropdowns(*args):
    drops = prototype_data.dropdown_expressions()
    return [
        (("noise-property." + exp_name,), Dropdown(l, name=exp_name))
        for exp_name, l in drops.items()
    ]


def make_hard_coded_terrain(control: str):
    return fa_menu.Menu(
        title=(f"gui-map-generator.{control}",),
        desc=lambda control=control: get_aux_desc(control),
        items=[
            j_float(
                title=("gui-map-generator.scale",),
                desc=("gui-map-generator.terrain-scale-description"),
                path=(BASIC, PROPERTY_EXPRESSION_NAMES, f"control:{control}:frequency"),
            ),
            j_float(
                title=("gui-map-generator.bias",),
                desc=("gui-map-generator.terrain-bias-description"),
                default=0,
                val=0,
                path=(BASIC, PROPERTY_EXPRESSION_NAMES, f"control:{control}:bias"),
            ),
        ],
    )


def get_dropdown_title(expression_property_name: str, *args):
    return ("noise-property." + expression_property_name,)


def get_dropdown_items(dropdown_List: Dropdown, *args):
    return [(e.localised_name, e.name) for e in dropdown_List]


resource_menu = {
    "expanded_resources": autoplace_menu(
        get_resources,
        [
            j_float(
                title=("gui-map-generator.frequency",),
                desc=("gui-map-generator.resource-frequency-description",),
                path=(BASIC, AUTO, "_arg", "frequency"),
            ),
            j_float(
                title=("gui-map-generator.size",),
                desc=("gui-map-generator.resource-size-description",),
                path=(BASIC, AUTO, "_arg", "size"),
            ),
            j_float(
                title=("gui-map-generator.richness",),
                desc=("gui-map-generator.resource-richness-description",),
                path=(BASIC, AUTO, "_arg", "richness"),
            ),
        ],
    )
}

expanding_noise_expressions = {}

expanding_autoplace_terrain = autoplace_menu(
    get_terrain,
    [
        j_float(
            title=("gui-map-generator.frequency",),
            desc=("gui-map-generator.resource-frequency-description",),
            path=(BASIC, AUTO, "_arg", "frequency"),
        ),
        j_float(
            title=("gui-map-generator.size",),
            desc=("gui-map-generator.resource-size-description",),
            path=(BASIC, AUTO, "_arg", "size"),
        ),
    ],
)
expanding_cliffs = autoplace_menu(
    get_cliffs,
    [
        j_float(
            title=("gui-map-generator.cliff-frequency",),
            desc=("gui-map-generator.cliff-frequency-description",),
            path=(BASIC, AUTO, "_arg", "frequency"),
        ),
        j_float(
            title=("gui-map-generator.cliff-continuity",),
            desc=("gui-map-generator.cliff-continuity-description",),
            path=(BASIC, AUTO, "_arg", "size"),
        ),
    ],
)

expanding_dropdowns = expanding_downdown_menu(
    title=get_dropdowns,
    items=get_dropdown_items,
    path=(BASIC, PROPERTY_EXPRESSION_NAMES, "_arg"),
)


terrain_menu = {
    "expanded_auto": expanding_dropdowns,
    "expanded_autoplace": expanding_autoplace_terrain,
    "expanded_cliffs": expanding_cliffs,
    "moisture": make_hard_coded_terrain("moisture"),
    "aux": make_hard_coded_terrain("aux"),
}

expanding_enemy_menu = autoplace_menu(
    get_enemy,
    [
        j_float(
            title=("gui-map-generator.frequency",),
            desc=("gui-map-generator.enemy-frequency-description",),
            default=1,
            val=1,
            path=(BASIC, AUTO, "_arg", "frequency"),
        ),
        j_float(
            title=("gui-map-generator.size",),
            desc=("gui-map-generator.enemy-size-description",),
            default=1,
            val=1,
            path=(BASIC, AUTO, "_arg", "size"),
        ),
    ],
)

enemy_menu = {
    "expanded_autoplace": expanding_enemy_menu,
    # todo no enemies
    "peaceful_mode": j_bool(
        ("gui-map-generator.peaceful-mode-checkbox",),
        ("gui-map-generator.peaceful-mode-description",),
        path=(BASIC, "peaceful_mode"),
    ),
    "starting_area": j_float(
        ("gui-map-generator.starting-area-size",),
        ("gui-map-generator.starting-area-size-description",),
        path=(BASIC, "starting_area"),
    ),
    "expansion": j_enable_disable_menu(
        name=("gui-map-generator.enemy-expansion-group-tile",),
        desc=("gui-map-generator.enemy-expansion-group-tile-description",),
        submenu=evolution_subs,
        path=(ADVANCED, "enemy_expansion", "enabled"),
    ),
    "evolution": j_enable_disable_menu(
        name=("gui-map-generator.evolution",),
        submenu=evolution_subs,
        path=(ADVANCED, "enemy_evolution", "enabled"),
        desc=("gui-map-generator.evolution-description",),
    ),
}

advanced_menu = {
    ("gui-map-generator.map-size-group-tile",): {
        "width": j_float(("gui-map-generator.map-width",), path=(BASIC, "width")),
        "height": j_float(("gui-map-generator.map-height",), path=(BASIC, "height")),
    },
    "technology_price_multiplier": j_float(
        ("gui-map-generator.price-multiplier",),
        path=(ADVANCED, "difficulty", "technology_price_multiplier"),
    ),
    "pollution": j_enable_disable_menu(
        name=("gui-map-generator.pollution",),
        submenu=pollution_subs,
        path=(ADVANCED, "pollution", "enabled"),
        desc=("gui-map-generator.pollution-description",),
    ),
    # todo:asteroids,
    # todo:spoiling,
}

customize_menu, _ = fa_menu.parse_menu_dict(
    {
        ("gui-map-generator.resources-tab-title",): resource_menu,
        ("gui-map-generator.terrain-tab-title",): terrain_menu,
        ("gui-map-generator.enemy-tab-title",): enemy_menu,
        ("gui-map-generator.advanced-tab-title",): advanced_menu,
        ("gui-map-generator.play",): launch_new_custom,
    }
)


map_menu = {
    get_presets: {
        "_desc": get_preset_desc,
        ("gui-map-generator.play",): launch_new_preset,
        "customize": set_preset_for_customize(
            title=("fa-l.customize-map-settings",), items=customize_menu
        ),
    },
}
