from typing import Any, Callable
import re
import weakref

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


def placeholder(*args):
    input("Feature under development, press enter to return.")
    return 0


def do_menu(branch, name, zero_item=("Back", 0)):
    if callable(branch):
        return branch()
    if zero_item:
        old_b = branch
        branch = {zero_item[0]: zero_item[1]}
        branch.update(old_b)
    while True:
        expanded_branch = {}
        for option, result in branch.items():
            if callable(option):
                generated_menu = option()
                if not generated_menu:
                    continue
                if type(generated_menu) == str:
                    expanded_branch[generated_menu] = result
                else:
                    for opt, res in option().items():
                        expanded_branch[opt] = lambda res=res: result(res)
            else:
                expanded_branch[option] = result
        keys = list(expanded_branch)
        opt = select_option(keys, prompt=f"{name}:", one_indexed=not zero_item)
        if zero_item and opt == 0:
            return zero_item[1]
        key = keys[opt]
        ret = do_menu(expanded_branch[key], key)
        try:
            if ret > 0 and zero_item and zero_item[1] == 0:
                return ret - 1
        except:
            print(expanded_branch[key], key, "returned", ret)
            raise ValueError()


back_menu_item = None


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
    def __init__(self, call: Callable, title=localised_str, back_levels=1):
        self.call = call
        self.back_levels = back_levels
        self._title = title

    def __call__(self, *args: Any) -> Any:
        self.call(*args)
        return self.back_levels


class VariableMenuMixIn(object):
    def get_items(self, *args):
        mapping = self._title(*args)
        self.last_reverse_map = {val: name for name, val in mapping.items()}
        return {name: (val,) for name, val in mapping.items()}

    def get_title(self, my_arg, *args):
        return self.last_reverse_map[my_arg]

    def get_desc(self, my_arg, *args):
        desc = self._desc
        if callable(desc):
            desc = desc(my_arg)
        return desc


back_item = Menu_function_leaf(back_func, ("gui.cancel",))


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


class menu_item(object):
    __slots__ = ["name", "submenu", "desc", "add_back"]

    def __init__(
        self,
        name: localised_str | Callable | dict,
        submenu: Callable | dict,
        desc: localised_str | None = None,
        add_back=True,
    ) -> None:
        self.add_back = add_back
        self.name = name
        self.desc = desc
        if isinstance(submenu, dict):
            arr_sub = []
            for sub_name, sub in submenu.items():

                if isinstance(sub, menu_item):
                    arr_sub.append(sub)
                    continue
                if isinstance(sub_name, str) and sub_name.startswith("_desc"):
                    self.desc = sub
                    continue
                arr_sub.append(menu_item(sub_name, sub))
            submenu = arr_sub
        self.submenu = submenu
        if not callable(self.submenu) and add_back:
            self.submenu = [back_menu_item] + self.submenu

    def get_names(self, *args):
        if callable(self.name):
            return self.name(*args)
        return self.name

    def get_menu_name(self, *args):
        if callable(self.name):
            return self.name(*args)
        return self.name

    def get_header(self, *args):
        ret = self.get_menu_name(*args)
        if self.desc is not None:
            if callable(self.desc):
                add = self.desc(*args)
            else:
                add = self.desc
            ret = ("", ret, "\n", add)
        return ret

    def __call__(self, *args):
        if callable(self.submenu):
            ret = self.submenu(*args)
            try:
                ret = int(ret)
            except:
                print(self.submenu, "returned a non integer with arguments:", args)
                raise ValueError()
            return ret
        while True:
            options = {}
            for submenu in self.submenu:
                sub_options = submenu.get_names(*args)
                if isinstance(sub_options, dict):
                    for sub_name, sub_arg in sub_options.items():
                        options[sub_name] = (submenu, (sub_arg,))
                else:
                    options[sub_options] = (submenu, ())
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
            ret = selected_menu(*(args + arg))
            if ret > 0 and self.add_back:
                return ret - 1


back_menu_item = menu_item(("gui.cancel",), back_func, False)


class setting_menu(menu_item):
    __slots__ = ["my_name", "desc", "default", "val", "submenu"]

    def __init__(
        self,
        name: localised_str,
        desc: localised_str | None = None,
        default: Any = "",
        val: Any = "",
    ) -> None:
        self.my_name = name
        self.desc = desc
        self.default = default
        self.val = val
        # self.submenu = self.edit

    def name(self, *args):
        return ("", self.my_name, ":", self.val_to_string())

    def get_options(self):
        pass

    def input_to_val(self, inp: str):
        pass

    def val_to_string(self):
        return str(self.val)

    def __call__(self, *args):
        while True:
            t_print(self.get_header(*args))
            t_print(("fa-l.current-setting", self.val_to_string()))
            potential_val = input(translate(("fa-l.new-setting-prompt",)))
            if potential_val:
                try:
                    self.input_to_val(potential_val.strip())
                except:
                    print("Invalid value")
                    continue
            return 0


class setting_menu_str(setting_menu):
    def __init__(
        self, name: localised_str, desc: localised_str | None, default: str, val: str
    ) -> None:
        super().__init__(name, desc, default, val)

    def input_to_val(self, inp: str):
        self.val = inp


class setting_menu_int(setting_menu):
    def __init__(
        self,
        name: localised_str,
        desc: localised_str | None = None,
        default: int = 0,
        val: int = 0,
    ) -> None:
        super().__init__(name, desc, default, val)

    def input_to_val(self, inp: str):
        self.val = int(inp)


class setting_menu_float(setting_menu):
    def __init__(
        self,
        name: localised_str,
        desc: localised_str | None = None,
        default: float = 1,
        val: float = 1,
    ) -> None:
        super().__init__(name, desc, default, val)

    def input_to_val(self, inp: str):
        self.val = float(inp)


class setting_menu_bool(setting_menu):
    def __init__(
        self,
        name: localised_str,
        desc: localised_str | None = None,
        default=True,
        val=True,
    ) -> None:
        super().__init__(name, desc, default, val)

    def val_to_string(self):
        return translate(
            ("gui-map-generator.enabled",)
            if self.val
            else ("gui-mod-info.status-disabled",)
        )

    def name(self, *args):
        ret = ("", self.my_name, ":", self.val_to_string())
        if self.desc:
            ret = ret + (" ", self.desc)
        return ret

    def __call__(self, *args):
        self.val = not self.val
        return 0


class setting_menu_option(menu_item):
    def __init__(self, name: localised_str, val, desc=None) -> None:
        self.name = name
        self.val = val
        self.desc = desc

    def get_names(self, *args):
        if self.desc:
            return ("", self.name, ":", self.desc)
        return self.name

    def __call__(self, *args):
        self.parent().val = self.val
        return 1


class setting_menu_options(setting_menu):
    def __init__(
        self,
        name: localised_str,
        submenu: dict,
        desc: localised_str | None = None,
        default: Any = "",
        val: Any = "",
    ) -> None:
        super().__init__(name, desc, default, val)
        self.submenu = [
            (
                sub_val
                if isinstance(sub_val, setting_menu_option)
                else setting_menu_option(sub_name, sub_val)
            )
            for sub_name, sub_val in submenu.items()
        ]
        for sub in self.submenu:
            sub.parent = weakref.ref(self)
        self.add_back = True
        self.submenu = [back_menu_item] + self.submenu

    def val_to_string(self):
        maybe = [sub.name for sub in self.submenu[1:] if sub.val == self.val]
        if len(maybe):
            return translate(maybe[0])
        return self.val

    def __call__(self, *args):
        return menu_item.__call__(self, *args)
