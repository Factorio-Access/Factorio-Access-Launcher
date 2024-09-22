import fa_menu
from fa_paths import MOD_NAME
from mods import mod_manager


class _mod_menu(fa_menu.Menu):
    def __call__(self, *args):
        with mod_manager:
            return super().__call__(*args)


class enable_disable_submenu(fa_menu.setting_menu_bool):
    def __init__(self):
        super().__init__(title=("gui-map-generator.enabled",))

    def val_to_string(self, *args):
        self.val = mod_manager.dict[args[-1]]["enabled"]
        return super().val_to_string(*args)

    def set_val(self, val, mod, *args):
        super().set_val(val, mod, *args)
        if self.val:
            mod_manager.enable(mod)
        else:
            mod_manager.disable(mod)
        return 0


def get_names(*args):
    if len(args):
        return args[-1]
    return get_mod_list()


def get_mod_list():
    ret = {}
    for name, data in mod_manager.dict.items():
        if data["enabled"]:
            status = ("gui-map-generator.enabled",)
        else:
            status = ("gui-mod-info.status-disabled",)
        display_name = ("", name, " (", status, ")")
        ret[display_name] = (name,)
    return ret


mod_menu = _mod_menu(
    ("gui-menu.mods",),
    fa_menu.parse_menu_dict({get_names: {"enabled": enable_disable_submenu()}})[0],
)


def check_for_main_mod():
    with mod_manager:
        if MOD_NAME not in mod_manager.dict:
            if fa_menu.getAffirmation(("fa-l.install-main-mod",)):
                mod_manager.install_mod(MOD_NAME)
        vers = mod_manager.by_name_version[MOD_NAME]
        latest_ver = max(vers)
        deps = vers[latest_ver].get_dependencies()
        for dep in deps:
            if not dep.type in ["?", "~", ""]:
                continue
            if dep.name in mod_manager.dict:
                continue
            mod_manager.install_mod(dep)
