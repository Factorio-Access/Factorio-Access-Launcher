import fa_menu
from fa_paths import MOD_NAME
from mods import mods, ModManager, Dependency, DependencyType, DepCheckResult
from translations import t_print


class _mod_menu(fa_menu.Menu):
    def __call__(self, *args):
        with mods as mod_manager:
            return super().__call__(mod_manager, *args)


class enable_disable_submenu(fa_menu.setting_menu_bool):
    def __init__(self):
        super().__init__(title=("gui-map-generator.enabled",))

    def val_to_string(self, *args):
        mod: str = args[0]
        mod_manager: ModManager = args[1]
        assert isinstance(mod_manager, ModManager)
        self.val = mod_manager.dict[mod]["enabled"]
        return super().val_to_string(*args[2:])

    def set_val(self, val, *args):
        mod: str = args[0]
        mod_manager: ModManager = args[1]
        super().set_val(val, mod, *args[2:])
        if self.val:
            mod_manager.enable(mod)
        else:
            mod_manager.disable(mod)


def get_names(*args):
    return get_mod_list(*args)


def get_mod_list(*args):
    mod_manager: ModManager = args[0]
    assert isinstance(mod_manager, ModManager)
    ret = []
    for name, data in mod_manager.dict.items():
        if data["enabled"]:
            status = ("gui-map-generator.enabled",)
        else:
            status = ("gui-mod-info.status-disabled",)
        display_name = ("", name, " (", status, ")")
        ret.append((display_name, name))
    return ret


def check_for_updates(*args):
    mod_manager: ModManager = args[0]
    actions = mod_manager.check_updates()
    if DepCheckResult.OK in actions:
        del actions[DepCheckResult.OK]
    if actions:
        for action in DepCheckResult:
            my_actions = actions[action]
            if not my_actions:
                continue
            print(action)
            for i in my_actions:
                print("    ", i)
        mod_manager.exec_dep_check_res(actions)
    else:
        t_print(("gui-update.no-new-updates",))
    return 0


mod_menu = _mod_menu(
    ("gui-menu.mods",),
    fa_menu.parse_menu_dict(
        {
            ("gui-update.check-updates-now",): check_for_updates,
            get_names: {"enabled": enable_disable_submenu()},
        }
    )[0],
)


def check_for_main_mod():
    with mods as mod_manager:
        if MOD_NAME in mod_manager.dict:
            return
        if not fa_menu.getAffirmation(("fa-l.install-main-mod",)):
            return
        print("Installing main mod:", MOD_NAME)
        dep = Dependency.from_str(MOD_NAME)
        mod = mod_manager.install_mod(dep)
        orig_deps = mod.dependencies.values()
        # make optional normal
        deps = (Dependency.from_str(str(d).strip("? ")) for d in orig_deps)
        all_deps = mod_manager.expand_dependencies(deps)
        res = mod_manager.check_deps(all_deps)
        mod_manager.exec_dep_check_res(res)
