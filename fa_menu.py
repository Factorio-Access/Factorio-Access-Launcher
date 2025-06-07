from typing import Any, Callable, Sequence, List
import weakref
import abc

from fa_arg_parse import d_print
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


ItemData = list[tuple[localised_str] | tuple[localised_str, Any]]
ItemDataFunc = Callable[..., ItemData]
Title = localised_str | ItemDataFunc
DescFunc = Callable[..., localised_str | None]


class MenuBase(object):
    def __init__(
        self,
        title: Title,
        desc: localised_str | DescFunc | None = None,
    ):
        self._title: ItemDataFunc = (
            title if callable(title) else lambda *args: [(title,)]
        )
        self._desc: DescFunc = desc if callable(desc) else lambda *args: desc

    def get_items(self, *args):
        self._last_map = self._title(*args)
        return self._last_map

    def get_title(self, *args):
        for i in self._last_map:
            a = i[1:]  # option args
            b = args[: len(a)]  # our args that might match
            if a == b:
                return i[0]
        raise ValueError("Value not found")

    def get_desc(self, *args):
        return self._desc(*args)

    def get_header(self, *args) -> localised_str:
        ret: localised_str = self.get_title(*args)
        desc = self.get_desc(*args)
        if desc is not None:
            ret = ("", ret, "\n", desc)
        return ret

    @abc.abstractmethod
    def __call__(self, *args: Any) -> int:
        pass


class Menu(MenuBase):
    def __init__(
        self,
        title: Title,
        items: List["MenuBase"],
        desc: localised_str | DescFunc | None = None,
        add_back=True,
    ):
        super().__init__(title=title, desc=desc)
        self.items = items.copy()
        self.add_back = add_back
        if add_back:
            self.items.insert(0, back_item)
        pass

    def __call__(self, *args):
        while True:
            options = []
            keys = []
            for submenu in self.items:
                sub_options = submenu.get_items(*args)
                for sub in sub_options:
                    keys.append(sub[0])
                    options.append((submenu, sub[1:]))
            opts = [translate(key) for key in keys]
            opt = select_option(
                opts,
                prompt=translate(self.get_header(*args)),
                one_indexed=not self.add_back,
            )
            selected_menu, arg = options[opt]
            ret = selected_menu(*(arg + args))
            if ret > 0 and self.add_back:
                return ret - 1


class Menu_function_leaf(MenuBase):
    def __init__(
        self, call: Callable, title: localised_str | ItemDataFunc, back_levels=1
    ):
        self.call = call
        self.back_levels = back_levels
        super().__init__(title=title)

    def __call__(self, *args: Any) -> Any:
        ret = self.call(*args)
        if isinstance(ret, int):
            return ret
        return self.back_levels


back_item = Menu_function_leaf(back_func, ("gui.cancel",))


def parse_menu_dict(menu: dict[Title, Any]):
    subs: list[MenuBase] = []
    desc: DescFunc | localised_str | None = None
    for t, sub in menu.items():
        if t == "_desc":
            desc = sub
            continue
        if isinstance(sub, Menu):
            subs.append(sub)
            continue
        subs.append(new_menu(t, sub, False))
    return subs, desc


def new_menu(title: Title, menu: dict | Callable, top_level=True):
    if isinstance(menu, dict):
        subs, desc = parse_menu_dict(menu)
        ret = Menu(title, subs, desc, not top_level)
        if top_level:
            ret.get_items()
        return ret
    if callable(menu):
        return Menu_function_leaf(menu, title)
    raise ValueError("Unexpected menu item:", menu)


class setting_menu(Menu):
    def __init__(
        self,
        title: localised_str,
        desc: localised_str | None = None,
        default: Any = "",
        val: Any = "",
    ) -> None:
        super().__init__(title=title, desc=desc, items=[], add_back=False)
        self.default = default
        self.val = val

    def get_items(self, *args) -> ItemData:
        data = super().get_items(*args)
        return [
            (
                (
                    "",
                    d[0],
                    ":",
                    self.val_to_string(*(d[1:] + args)),
                ),
            )
            + d[1:]
            for d in data
        ]

    def input_to_val(self, inp: str, *args) -> Any:
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
        ret: ItemData = []
        for data in super().get_items(*args):
            desc = self._desc(*(data[1:] + args))
            name = ("", data[0], " ", desc) if desc is not None else data[0]
            ret.append((name,) + data[1:])
        return ret

    def __call__(self, *args):
        self.set_val(not self.val, *args)
        return 0


class setting_menu_option(Menu_function_leaf):
    def __init__(
        self, parent: "setting_menu_options", options: ItemDataFunc, **kwargs
    ) -> None:
        self.parent = weakref.ref(parent)
        super().__init__(call=self.set_parents_val, title=options, **kwargs)

    def set_parents_val(self, val, *args):
        parent = self.parent()
        if not parent:
            raise Exception("whoops!")
        parent.set_val(val, *args)
        return 1


class setting_menu_options(setting_menu):
    def __init__(
        self,
        title: localised_str,
        items: Callable | list[tuple],
        desc: localised_str | None = None,
        default: Any = None,
        val: Any = None,
        child_class=setting_menu_option,
    ) -> None:
        if not callable(items):
            items = lambda: items
        menu_items: list[MenuBase] = [child_class(self, items)]
        Menu.__init__(self, title, menu_items, desc)
        self.default = default
        if val is not None:
            self.set_val(val)

    def __call__(self, *args):
        return Menu.__call__(self, *args)
