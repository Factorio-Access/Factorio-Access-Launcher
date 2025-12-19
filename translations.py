import re
from typing import Iterable, Union, Callable
from collections import defaultdict, UserDict
from collections.abc import Sequence
import os
import zipfile
from pathlib import Path
import json

from fa_arg_parse import d_print
import config

# cSpell:words leftshoulder rightshoulder

localised_str = Union[str, Sequence["localised_str"]]


def get_control(name: str) -> list[str]:
    if input_type == joy:
        has_alt = name.endswith(alt)
        if has_alt:
            name = name.removesuffix(alt)
        if not name.endswith(con):
            name += con
        if has_alt:
            name += alt
    with config.current_conf:
        return config.current_conf.get_setting("controls", name).split(" + ")


def t_control(control_name, alt_type=0):
    cont = get_control(control_name)
    if len(cont) == 1 and cont[0] == "":
        return translate(["controls.not-set"])
    return "+".join(
        (translate(["?", ["control-key." + key.lower()], key]) for key in cont)
    )


def t_modifier(control_name):
    cont = get_control(control_name)
    if len(cont) <= 1:
        return translate(["no-modifier-selected"])
    return "".join((translate(tuple(["control-keys." + key] for key in cont[:-1]))))


def t_alt_control(alt_type, control_name):
    return t_control(control_name, alt_type)


def t_move():
    pass


def t_entity(name):
    pass


def t_item(name):
    pass


def t_tile(name):
    pass


def t_fluid(name):
    pass


def return_blank():
    return ""


knm = "keyboard-and-mouse"
joy = "game-controller"

con = "-controller"
alt = "-alternate"

input_type = knm


def do_controller_check():
    global input_type
    try:
        with config.current_conf as conf:
            input_type = conf.input.input_method
    except:
        pass


replacements = {
    "__CONTROL__name__": t_control,
    "__CONTROL__MODIFIER__name__": t_modifier,
    "__CONTROL_STYLE_BEGIN__": return_blank,
    "__CONTROL_STYLE_END__": return_blank,
    "__CONTROL_LEFT_CLICK__": {
        knm: ["control-keys.mouse-button-1"],
        joy: ["control-keys.controller-b"],
    },
    "__CONTROL_RIGHT_CLICK__": {
        knm: ["control-keys.mouse-button-2"],
        joy: ["control-keys.controller-x"],
    },
    "__CONTROL_KEY_SHIFT__": {
        knm: ["control-keys.shift"],
        joy: ["control-keys.controller-leftshoulder"],
    },
    "__CONTROL_KEY_CTRL__": {
        knm: ["control-keys.control"],
        joy: ["control-keys.controller-rightshoulder"],
    },
    "__ALT_CONTROL_LEFT_CLICK__n__": {
        knm: ["control-keys.mouse-button-1-alt-n"],
        joy: ["control-keys.controller-button-alt-n", ["control-keys.controller-b"]],
    },
    "__ALT_CONTROL_RIGHT_CLICK__n__": {
        knm: ["control-keys.mouse-button-2-alt-n"],
        joy: ["control-keys.controller-button-alt-n", ["control-keys.controller-x"]],
    },
    "__REMARK_COLOR_BEGIN__": return_blank,
    "__REMARK_COLOR_END__": return_blank,
    "__ALT_CONTROL__n__name__": t_alt_control,
    "__CONTROL_MOVE__": t_move,
    "__ENTITY__name__": t_entity,
    "__ITEM__name__": t_item,
    "__TILE__name__": t_tile,
    "__FLUID__name__": t_fluid,
}
replacement_functions: dict[str, tuple[int, Callable[..., str]]] = {}
for replace, r_with in replacements.items():
    key, *args = [p for p in replace.split("__") if p]
    if type(r_with) == dict:
        if "n" in args:
            r_with = lambda n, d=r_with: do_special(d, n)
        else:
            r_with = lambda d=r_with: do_special(d)
    replacement_functions[key] = (len(args), r_with)


def do_special(special, n=0):
    return translate(special[input_type], n)


class MissingTranslation(LookupError):
    pass


def translate(l_str: localised_str, n=0, error=False) -> str:
    if type(l_str) == str:
        return l_str
    try:
        key, *args = l_str
    except:
        return str(l_str)
    if not isinstance(key, str):
        raise ValueError("localised string key must be a string, but got:", key)
    if key == "":
        return "".join((translate(arg) for arg in args))
    if key == "?":
        for attempt in args:
            try:
                return translate(attempt, error=True)
            except MissingTranslation:
                pass
        return translate(args[-1])
    try:
        cat, key = key.split(".", 1)
    except:
        cat = ""
    if n:
        key = re.sub(r"\bn\b", str(n), key)
    if key not in translation_table[cat]:
        if error:
            raise MissingTranslation(cat, key)
        return f'Unknown key: "{cat}.{key}"'
    return expand(translation_table[cat][key], args)


translation_table = defaultdict(dict)


class translated_args(dict):
    def __init__(self, args: list[localised_str]):
        self.args = args
        super().__init__()

    def __missing__(self, key):
        try:
            arg = self.args[int(key) - 1]
        except (ValueError, IndexError):
            val = f"__{key}__"
        else:
            val = translate(arg)
        self[key] = val
        return self[key]


plural_compat = re.compile(r"__plural_for_parameter_(\d+)_{")


def plural_compat_replacer(m: re.Match):
    return "__plural_for_parameter__" + m[1] + "__{"


def expand(template: str, args: list[localised_str] = []) -> str:
    template = plural_compat.sub(plural_compat_replacer, template)
    parts = template.split("__")
    ret, _ = expand_r(parts, translated_args(args))
    return ret


def expand_r(
    parts: list[str], t_args: translated_args, in_plural=False
) -> tuple[str, str]:
    ret = ""
    stray__ = False
    while parts:
        p = parts.pop(0)
        if p in replacement_functions:
            num_args, rep_func = replacement_functions[p]
            args, parts = parts[:num_args], parts[num_args:]
            ret += rep_func(*args)
        elif p == "plural_for_parameter":
            arg_num = parts.pop(0)
            my_num = t_args[arg_num]
            remaining = parts.pop(0)
            assert remaining[0] == "{", "Unexpected start of plural. Expected {"
            remaining = remaining[1:]
            matched = False
            while remaining:
                condition, remaining = remaining.split("=", 1)
                assert type(remaining) == str
                parts.insert(0, remaining)
                temp_res, remaining = expand_r(parts, t_args, True)
                if not matched:
                    matched = True
                    for cond in condition.split(","):
                        if cond == "rest":
                            break
                        if my_num == cond:
                            break
                        if "ends in " in cond:
                            check = cond[8:]
                            if my_num.endswith(check):
                                break
                    else:
                        matched = False
                    if matched:
                        ret += temp_res
        elif p.isdigit():
            ret += t_args[p]
        else:
            if "|" in p or "}" in p and in_plural:
                p, add_back = re.split(r"}|\|", p, 1)
                ret += p
                return ret, add_back
            if stray__:
                ret += "__"
            ret += p
            stray__ = True
            continue
        stray__ = False
    return ret, ""


fancy = re.compile(r"[*.?()\[\]]")


def get_mod_path_parts(path: Union[zipfile.Path, Path]):
    import fa_paths

    if isinstance(path, Path):
        try:
            return path.relative_to(fa_paths.MODS()).parts
        except:
            pass
        return path.relative_to(fa_paths.READ_DIR()).parts
    parts = []
    while isinstance(path.parent, zipfile.Path):
        parts.append(path.name)
        path = path.parent
    return tuple(parts[::-1])


def read_cfg(fp: Iterable[str], conf=False, ret=defaultdict(dict)):
    name = ""
    while True:
        current_cat = ret[name]
        for line in fp:
            if line[0] == "[":
                name = line[1 : line.find("]")].strip()
                break
            part = line.split("=", 1)
            if len(part) == 2:
                key = part[0]
                if conf:
                    key = key.lstrip("; ")
                if key[0] == "#":
                    continue
                if key[0] == ";":
                    continue
                current_cat[key] = part[1].rstrip().replace(r"\n", "\n")
        else:
            return ret


check_cats = {
    "multiplayer-lobby": ["config-output", "config-help", "gui-multiplayer-lobby"],
    "map-view": ["gui-map-view-settings"],
    "controls": ["controls"],
    "graphics": ["gui-graphics-settings"],
    "interface": ["gui-interface-settings"],
    "other": ["gui-other-settings"],
    "sound": ["gui-sound-settings"],
    "general": ["gui-interface-settings"],
    "input": ["gui-interface-input"],
}


def check_config_locale():
    import fa_paths

    with (fa_paths.READ_DIR() / "core/locale/en/core.cfg").open(encoding="utf8") as fp:
        translations = read_cfg(fp)
    with fa_paths.CONFIG().open(encoding="utf8") as fp:
        config = read_cfg(fp, conf=True)
    cross_cats = defaultdict(lambda: defaultdict(list))
    for cat, configs in config.items():
        if cat in check_cats:
            t_to_check = {
                t_cat: tlist
                for t_cat, tlist in translations.items()
                if t_cat in check_cats[cat]
            }
        else:
            t_to_check = {}
        for config_key in configs.keys():
            if config_key[-12:] == "-alternative":
                continue
            found = False
            for t_cat, trans in t_to_check.items():
                if config_key in trans:
                    found = True
                    break
            if not found:
                for t_cat, trans in translations.items():
                    if config_key in trans:
                        cross_cats[cat][t_cat] += [(config_key, trans[config_key])]
                        found = True
                if not found:
                    print(f"missing:{cat}.{config_key}")
    for c_cat, t_cats in cross_cats.items():
        print(c_cat)
        for t_cat, count in t_cats.items():
            print("\t", t_cat, count)


def maybe_load(path: Path | zipfile.Path):
    try:
        with path.open(encoding="utf8") as fp:
            read_cfg(fp, ret=translation_table)
    except FileNotFoundError:
        pass


def load_init(code):
    cfg = Path(__file__).parent.joinpath("r", "locale", code + ".cfg")
    maybe_load(cfg)


def load_full(code):
    load_init(code)
    from fa_paths import READ_DIR

    cfg = READ_DIR() / "core" / "locale" / code / "core.cfg"
    maybe_load(cfg)
    from mods import mods

    with mods as mod_manager:
        for cfg in mod_manager.iter_mod_files("locale/" + code + "/.*.cfg"):
            maybe_load(cfg)


def get_langs():
    lang = {}
    reg = re.compile(r"locale/([\w-]+)/info.json")
    from fa_paths import READ_DIR

    locs = READ_DIR() / "core" / "locale"
    for path in locs.iterdir():
        code = path.name
        with (path / "info.json").open(encoding="utf8") as fp:
            info = json.load(fp)
        if "language-name" in info:
            lang[code] = info["language-name"]
    return lang


def t_print(*args, **kwargs):
    print(*(translate(arg) for arg in args), **kwargs)


code = "en"
load_init("en")


def check_lang():
    global code
    load_full("en")
    with config.current_conf as conf:
        code = conf.general.locale
        if not code or code == "auto":
            import locale
            import fa_menu
            import sys

            if sys.platform == "win32":
                import ctypes

                loc = locale.windows_locale[
                    ctypes.windll.kernel32.GetUserDefaultUILanguage()
                ]
            else:
                loc, enc = locale.getlocale()
            langs = get_langs()
            short_list = []
            if loc is not None and len(loc) > 1:
                for code, lang in langs.items():
                    if loc.startswith(code) or lang in loc:
                        short_list.append(code)
            if len(short_list):
                if len(short_list) == 1:
                    code = short_list[0]
                    load_full(code)
                    op = fa_menu.select_option(
                        [("gui.confirm",), ("fa-l.list-all-langs",)],
                        ("fa-l.guessed-language", langs[code]),
                    )
                    if op == 0:
                        conf.general.locale = code
                        return
                else:
                    d_print("We got a short list for langs", short_list)
            lang_op = fa_menu.select_option(
                langs.values(), ("gui-interface-settings.locale",)
            )
            conf.general.locale = list(langs.keys())[lang_op]
        load_full(conf.general.locale)


if __name__ == "__main__":
    check_lang()
