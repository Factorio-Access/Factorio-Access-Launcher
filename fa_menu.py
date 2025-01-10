from typing import Any, Callable

from translations import translate, localised_str, t_print
import fa_paths
from fa_arg_parse import args


def getAffirmation(prompt=""):
    while True:
        i = input(translate(prompt))
        if i == "yes" or i == "Yes" or i == "YES" or i == "y" or i == "Y":
            return True
        elif i == "no" or i == "No" or i == "n" or i == "N" or i == "NO":
            return False
        else:
            print("Invalid input, please type either Yes or No")


def getBoolean():
    while True:
        i = input()
        if i == "true" or i == "True" or i == "t" or i == "T" or i == "TRUE":
            return "true"
        elif i == "false" or i == "False" or i == "f" or i == "F" or i == "FALSE":
            return "false"
        else:
            print("Invalid input, please type either true or false")


def getNum():
    while True:
        i = input()
        try:
            result = float(i)
            return str(result)
        except:
            print("Invalid input, please enter a number.\n")


def select_option(options, prompt="Select an option:", one_indexed=True):
    pre_prompt = None
    while True:
        # print("\033c", end="")
        if pre_prompt:
            t_print(pre_prompt)
        t_print(prompt)
        for i, val in enumerate(options):
            t_print(f"{i + one_indexed}:", val)
        i = input()
        if not i.isdigit():
            if i == "debug":
                args.fa_debug = True
                print("debug output")
                for name, path in fa_paths.__dict__.items():
                    if type(path) == str:
                        print(f"{name:20}:{path}")

            pre_prompt = "Invalid input, please enter a number."
            continue
        i = int(i) - one_indexed
        if i >= len(options):
            pre_prompt = "Option too high, please enter a smaller number."
            continue
        if i < 0:
            pre_prompt = "Options start at 1. Please enter a larger number."
            continue
        return i


def back_func(*args):
    return 1


class Menu(object):
    def __init__(
        self,
        title: localised_str,
        items: list["Menu"],
        desc: localised_str = None,
        add_back=True,
    ):
        self._title = title
        self.items = items.copy()
        self._desc = desc
        self.add_back = add_back
        if add_back:
            self.items.insert(0, back_item)
        pass

    def get_items(self, *args):
        return {self._title: ()}

    def get_title(self, *args):
        return self._title

    def get_desc(self, *args):
        return self._desc

    def get_header(self, *args):
        ret = self.get_title(*args)
        desc = self.get_desc(*args)
        if desc is not None:
            ret = ("", ret, "\n", desc)
        return ret

    def __call__(self, *args):
        while True:
            options = {}
            for submenu in self.items:
                sub_options = submenu.get_items(*args)
                for sub_name, sub_arg in sub_options.items():
                    options[sub_name] = (submenu, sub_arg)
            keys = list(options)
            opts = [translate(key) for key in keys]
            selected_menu, arg = options[
                keys[
                    select_option(
                        opts,
                        prompt=translate(self.get_header(*args)),
                        one_indexed=not self.add_back,
                    )
                ]
            ]
            ret = selected_menu(*(arg + args))
            if ret > 0 and self.add_back:
                return ret - 1


class Menu_function_leaf(Menu):
    def __init__(self, call: Callable, title: localised_str, back_levels=1):
        self.call = call
        self.back_levels = back_levels
        self._title = title

    def __call__(self, *args: Any) -> Any:
        ret = self.call(*args)
        if isinstance(ret, int):
            return ret
        return self.back_levels


back_item = Menu_function_leaf(back_func, ("gui.cancel",))


class VariableMenuMixIn(object):
    def get_items(self, *args):
        self.last_map = self._title(*args)
        return self.last_map

    def get_title(self, my_arg, *args):
        for name, val in self.last_map.items():
            if val[0] == my_arg:
                return name
        raise ValueError("Value not found")

    def get_desc(self, my_arg, *args):
        desc = self._desc
        if callable(desc):
            desc = desc(my_arg)
        return desc


class Menu_var(VariableMenuMixIn, Menu):
    pass


class Menu_var_leaf(VariableMenuMixIn, Menu_function_leaf):
    pass


def parse_menu_dict(menu: dict):
    subs = []
    desc = None
    for t, sub in menu.items():
        if t == "_desc":
            desc = sub
            continue
        if isinstance(sub, Menu):
            subs.append(sub)
            continue
        subs.append(new_menu(t, sub, False))
    return subs, desc


def new_menu(title: localised_str, menu: dict | Callable, top_level=True):
    if isinstance(menu, dict):
        subs, desc = parse_menu_dict(menu)
        if callable(title):
            return Menu_var(title, subs, desc, not top_level)
        return Menu(title, subs, desc, not top_level)
    if callable(menu):
        if callable(title):
            return Menu_var_leaf(menu, title)
        return Menu_function_leaf(menu, title)
    raise ValueError("Unexpected menu item:", menu)


class setting_menu(Menu):
    __slots__ = ["my_title", "desc", "default", "val", "submenu"]

    def __init__(
        self,
        title: localised_str,
        desc: localised_str | None = None,
        default: Any = "",
        val: Any = "",
    ) -> None:
        self._title = title
        self._desc = desc
        self.default = default
        self.val = val
        # self.submenu = self.edit

    def get_items(self, *args):
        return {("", self._title, ":", self.val_to_string(*args)): ()}

    def input_to_val(self, inp: str, *args):
        return inp

    def val_to_string(self, *args):
        return str(self.val)

    def set_val(self, val, *args):
        self.val = val

    def __call__(self, *args):
        while True:
            t_print(self.get_header(*args))
            t_print(("fa-l.current-setting", self.val_to_string(*args)))
            potential_val = input(translate(("fa-l.new-setting-prompt",)))
            if potential_val:
                try:
                    val = self.input_to_val(potential_val.strip(), *args)
                except:
                    print("Invalid value")
                    continue
                self.set_val(val, *args)
            return 0


class setting_menu_str(setting_menu):
    def __init__(
        self, title: localised_str, desc: localised_str | None, default: str, val: str
    ) -> None:
        super().__init__(title, desc, default, val)


class setting_menu_int(setting_menu):
    def __init__(
        self,
        title: localised_str,
        desc: localised_str | None = None,
        default: int = 0,
        val: int = 0,
    ) -> None:
        super().__init__(title, desc, default, val)

    def input_to_val(self, inp: str, *args):
        return int(inp)


class setting_menu_float(setting_menu):
    def __init__(
        self,
        title: localised_str,
        desc: localised_str | None = None,
        default: float = 1,
        val: float = 1,
    ) -> None:
        super().__init__(title, desc, default, val)

    def input_to_val(self, inp: str, *args):
        return float(inp)


class setting_menu_bool(setting_menu):
    def __init__(
        self,
        title: localised_str,
        desc: localised_str | None = None,
        default=True,
        val=True,
    ) -> None:
        super().__init__(title, desc, default, val)

    def val_to_string(self, *args):
        return translate(
            ("gui-map-generator.enabled",)
            if self.val
            else ("gui-mod-info.status-disabled",)
        )

    def get_items(self, *args):
        ret = ("", self._title, ":", self.val_to_string(*args))
        if self._desc:
            ret = ret + (" ", self._desc)
        return {ret: ()}

    def __call__(self, *args):
        self.set_val(not self.val, *args)
        return 0


class setting_menu_option(Menu):
    def __init__(self, title: localised_str, val, desc=None) -> None:
        self._title = title
        self.val = val
        self._desc = desc

    def get_items(self, parent: "setting_menu_options", *args):
        ret = self._title
        if self._desc:
            ret = ("", self._title, ":", self._desc)
        return {ret: ()}

    def __call__(self, parent: "setting_menu_options", *args):
        parent.set_val(self.val)
        return 1


class setting_menu_options(setting_menu):
    def __init__(
        self,
        title: localised_str,
        items: dict,
        desc: localised_str | None = None,
        default: Any = "",
        val: Any = "",
    ) -> None:
        menu_items = [
            setting_menu_option(sub_name, sub_val)
            for sub_name, sub_val in items.items()
        ]
        Menu.__init__(self, title, menu_items, desc)
        self.default = default
        self.set_val(val)

    def val_to_string(self, *args):
        maybe = [sub._title for sub in self.items[1:] if sub.val == self.val]
        if len(maybe):
            return translate(maybe[0])
        return self.val

    def __call__(self, *args):
        # duplicate self is to pass the parent to the option
        return Menu.__call__(self, self, *args)
