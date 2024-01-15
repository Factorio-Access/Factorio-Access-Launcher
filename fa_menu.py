from typing import Any,Callable
import re
import weakref

from translations import translate,localised_str
import fa_paths
from fa_arg_parse import args

def getAffirmation():
    while True:
        i = input()
        if i == 'yes' or i == 'Yes' or i == 'YES' or i == 'y' or i == 'Y':
            return True
        elif i == 'no' or i == 'No' or i == 'n' or i == 'N' or i == 'NO':
            return False
        else:
            print("Invalid input, please type either Yes or No")


def getBoolean():
    while True:
        i = input()
        if i == 'true' or i == 'True' or i == 't' or i == 'T' or i == 'TRUE':
            return 'true'
        elif i == 'false' or i == 'False' or i == 'f' or i == 'F' or i == 'FALSE':
            return 'false'
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

def select_option(options,prompt='Select an option:',one_indexed=True):
    while True:
        print(prompt)
        for i, val in enumerate(options):
            print(i + one_indexed, ": ", val)    
        i=input()
        if not i.isdigit():
            if i=='debug':
                args.fa_debug = True
                print("debug output")
                for name,path in fa_paths.__dict__.items():
                    if type(path)==str:
                        print(f'{name:20}:{path}')

            print("Invalid input, please enter a number.")
            continue
        i=int(i)-one_indexed
        if i >= len(options):
            print("Option too high, please enter a smaller number.")
            continue
        if i<0:
            print("Options start at 1. Please enter a larger number.")
            continue
        return i

def back_func(*args):
    return 1

def do_menu(branch, name, zero_item=("Back",0)):
    if callable(branch):
        return branch()
    if zero_item:
        old_b = branch
        branch = {zero_item[0]:zero_item[1]}
        branch.update(old_b)
    while True:
        expanded_branch={}
        for option, result in branch.items():
            if callable(option):
                generated_menu=option()
                if not generated_menu:
                    continue
                if type(generated_menu)==str:
                    expanded_branch[generated_menu]=result
                else:
                    for opt, res in option().items():
                        expanded_branch[opt]=lambda res=res:result(res)
            else:
                expanded_branch[option]=result
        keys=list(expanded_branch)
        opt = select_option(keys, prompt=f"{name}:", one_indexed= not zero_item)
        if zero_item and opt==0:
            return zero_item[1]
        key = keys[opt]
        ret = do_menu(expanded_branch[key],key)
        try:
            if ret > 0 and zero_item and zero_item[1]==0:
                return ret-1
        except:
            print(expanded_branch[key],key,"returned",ret)
            raise ValueError()

back_menu_item=None

class menu_item(object):
    __slots__=["name","submenu","desc","add_back"]
    def __init__(self,
                 name:localised_str|Callable|dict,
                 submenu:Callable|dict,
                 desc:localised_str|None = None,
                 add_back=True) -> None:
        self.add_back=add_back
        self.name=name
        self.desc=desc
        if isinstance(submenu,dict):
            submenu=[subsubmenu if isinstance(subsubmenu,menu_item) else menu_item(sub_name,subsubmenu) for sub_name,subsubmenu in submenu.items()]
        self.submenu=submenu
        if not callable(self.submenu) and add_back:
            self.submenu=[back_menu_item]+self.submenu
    def get_names(self,*args):
        if callable(self.name):
            return self.name(*args)
        return self.name
    def get_menu_name(self,*args):
        if callable(self.name):
            return self.name(*args)
        return self.name
    def __call__(self,*args):
        if callable(self.submenu):
            ret = self.submenu(*args)
            try:
                ret=int(ret)
            except:
                print(self.submenu, "returned a non integer with arguments:", args)
                raise ValueError()
            return ret
        while True:
            this_name=self.get_menu_name(*args)
            if self.desc:
                this_name=('',this_name,'\n',self.desc)
            options={}
            for submenu in self.submenu:
                sub_options=submenu.get_names()
                if isinstance(sub_options,dict):
                    for sub_name, sub_arg in sub_options:
                        options[sub_name]=(submenu,(sub_arg,))
                else:
                    options[sub_options]=(submenu,())
            keys=list(options)
            opts=[translate(key) for key in keys]
            selected_menu,arg = options[keys[select_option(opts, prompt=translate(this_name), one_indexed= not self.add_back)]]
            ret = selected_menu(*(args+arg))
            if ret > 0:
                return ret-1
back_menu_item=menu_item("Back",back_func,False)

class setting_menu(menu_item):
    __slots__=["myname","desc","default","val","submenu"]
    def __init__(
            self,
            name:localised_str,
            desc:localised_str|None = None,
            default:Any = '',
            val:Any = '')-> None:
        self.myname = name
        self.desc = desc
        self.default = default
        self.val = val
        #self.submenu = self.edit
    def name(self,*args):
        return ("",self.myname,":",self.val_to_string())
    def get_options(self):
        pass
    def input_to_val(self,inp:str):
        pass
    def val_to_string(self):
        return str(self.val)
    def __call__(self):
        while True:
            print(translate(self.name()))
            if self.desc is not None:
                print(translate(self.desc))
            print(f"Current value:{self.val_to_string()}")
            potential_val=input("Enter new value below or leave blank to keep current value:")
            if potential_val:
                try:
                    self.input_to_val(potential_val.strip())
                except:
                    print("Invalid value")
                    continue
            return 0

class setting_menu_str(setting_menu):
    def __init__(self, name: localised_str, desc: localised_str | None, default: str, val: str) -> None:
        super().__init__(name, desc, default, val)
    def input_to_val(self, inp: str):
        self.val=inp

class setting_menu_int(setting_menu):
    def __init__(self, name: localised_str, desc: localised_str | None =None, default: int =0, val: int =0) -> None:
        super().__init__(name, desc, default, val)
    def input_to_val(self, inp: str):
        self.val=int(inp)

class setting_menu_float(setting_menu):
    def __init__(self, name: localised_str, desc: localised_str | None =None, default: float =1, val: float =1) -> None:
        super().__init__(name, desc, default, val)
    def input_to_val(self, inp: str):
        self.val=float(inp)

class setting_menu_bool(setting_menu):
    def __init__(self, name: localised_str , desc: localised_str | None =None, default=True, val=True) -> None:
        super().__init__(name, desc, default, val)
    def val_to_string(self):
        return translate(("gui-map-generator.enabled",) if self.val else ("gui-mod-info.status-disabled",))
    def name(self,*args):
        ret=("",self.myname,":",self.val_to_string())
        if self.desc:
            ret=ret+(" ",self.desc)
        return ret
    def __call__(self):
        self.val = not self.val
        return 0

class setting_menu_option(menu_item):
    def __init__(self, name: localised_str, val) -> None:
        self.name=name
        self.val=val
    def __call__(self, *args):
        self.parent().val = self.val
        return 1


class setting_menu_options(setting_menu):
    def __init__(self, name: localised_str, submenu:dict,desc: localised_str | None =None, default: Any = '', val: Any = '') -> None:
        super().__init__(name, desc, default, val)
        self.submenu = [setting_menu_option(subname,subval) for subname,subval in submenu.items()]
        for sub in self.submenu:
            sub.parent=weakref.ref(self)
        self.add_back=True
        self.submenu = [back_menu_item]+self.submenu
    def val_to_string(self):
        maybe=[sub.name for sub in self.submenu[1:] if sub.val==self.val]
        if len(maybe):
            return translate(maybe[0])
        return self.val
    def __call__(self):
        return menu_item.__call__(self)