import fa_paths

global debug
debug = False

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
                global debug
                debug=True
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
