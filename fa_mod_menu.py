import fa_menu
from fa_paths import MOD_NAME
from mods import mod_manager


class _mod_menu(fa_menu.Menu):
    def __call__(self, *args):
        with mod_manager:
            return super().__call__(*args)


class enable_disable_submenu(fa_menu.setting_menu_bool):
    def get_names(self, *args):
        self.val = mod_manager.dict[args[-1]]["enabled"]
        return super().get_names(*args)

    def __call__(self, *args):
        super().__call__(*args)
        if self.val:
            mod_manager.enable(args[0])
        else:
            mod_manager.disable(args[0])
        return 0


def get_names(*args):
    if len(args):
        return args[-1]
    return get_mod_list()


def get_mod_list():
    return {
        (
            "",
            name,
            " (",
            (
                ("gui-map-generator.enabled",)
                if data["enabled"]
                else ("gui-mod-info.status-disabled",)
            ),
            ")",
        ): name
        for name, data in mod_manager.dict.items()
    }


enable_menu_setting = enable_disable_submenu(
    ("gui-map-generator.enabled",), None, True, True
)
mod_menu = _mod_menu(
    ("gui-menu.mods",),
    fa_menu.parse_menu_dict({get_names: {"enabled": enable_menu_setting}})[0],
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
