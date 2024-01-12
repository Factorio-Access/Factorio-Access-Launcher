import os
import sys
import re
import subprocess
import shutil

import fa_menu
from __main__ import __file__ as main_file


if getattr(sys, 'frozen', False):
    MY_BIN = sys.executable
else:
    MY_BIN = main_file

MY_CONFIG_DIR = os.path.dirname(MY_BIN)
    

MAC="Darwin"
WIN="win32"
LIN="linux"

WRITE_DATA_MAP={
    MAC:'~/Library/Application Support/factorio',
    WIN:'%appdata%\Factorio',
    LIN:'~/.factorio'
}

BIN=''
if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
    BIN=sys.argv[1]
else:
    exe_map = {
        WIN:[
            "./bin/x64/factorio.exe",
            r"%ProgramFiles%\Factorio\bin\x64\factorio.exe",
            r'%ProgramFiles(x86)%\Steam\steamapps\common\Factorio\bin\x64\factorio.exe'
            ],
        MAC:[
            "/Applications/factorio.app/Contents/MacOS/factorio",
            '~/Library/Application Support/Steam/steamapps/common/Factorio/factorio.app/Contents/MacOS/factorio'
            ],
        LIN:[
            "./bin/x64/factorio",
            r'~/.steam/root/steam/steamapps/common/Factorio/bin/x64/factorio'
            ]
        }
    for path in exe_map[sys.platform]:
        path=os.path.expanduser(os.path.expandvars(path))
        if os.path.isfile(path):
            BIN = os.path.abspath(path)
            break
    if BIN.find('steam') >= 0:
        print("Looks like you have a steam installed version of factorio. Please launch through steam after updating it's command line parameters to the following:")
        print('"' + os.path.abspath(MY_BIN) + '" %command%')
        input("press enter to exit")
        raise SystemExit
if not BIN:
    input("Could not find factorio. If you've installed facorio in a standard way please contact the mod developers with your system details. If you're using the protable version please either place this launcher in the folder with the data and bin folders or launch with the factorio execuable path as an argument.")
    raise SystemExit

factorio_replacements={
    '__PATH__system-write-data__':os.path.expanduser(os.path.expandvars(WRITE_DATA_MAP[sys.platform])),
    '__PATH__executable__': os.path.dirname(BIN),
    '__PATH__system-read-data__': os.path.join(os.path.dirname(BIN),'..','..','data')
    }

def proccess(path):
    for k,v in factorio_replacements.items():
        path = path.replace(k,v)
    path = os.path.abspath(path)
    return path

config_path='config/config.ini'

configs=[]
if len(sys.argv) > 2 and os.path.isfile(sys.argv[2]):
    configs.append(sys.argv[2])
    
configs.append("./"+config_path)

#try to append another config path from config-path.cfg
try:
    fp=open(proccess('__PATH__executable__/../../config-path.cfg'),encoding='utf8')
except FileNotFoundError:
    configs.append(proccess(os.path.join('__PATH__system-write-data__',config_path)))
else:
    with fp:
        for line in fp:
            match = re.match(r'config-path=(.*)',line)
            if match:
                configs.append(os.path.join(proccess(match.group(1)),'config.ini'))
                break


CONFIG=''
WRITE_DIR=''
READ_DIR=''


def find_config():
    global CONFIG
    global WRITE_DIR
    global READ_DIR
    for path in configs:
        try:
            fp=open(path,encoding='utf8')
        except FileNotFoundError:
            continue
        CONFIG=path
        with fp:
            for line in fp:
                if match:=re.match(r'write-data=(.*)',line):
                    WRITE_DIR = proccess(match[1])
                if match:=re.match(r'read-data=(.*)',line):
                    READ_DIR = proccess(match[1])
                if WRITE_DIR and READ_DIR:
                    break
        break
find_config()
if not CONFIG:
    print('Unable to find the factorio config. Would you like to create a configuration in the default location?')
    if fa_menu.getAffirmation():
        print("Creating Config, this will take while.")
        facotrio_process=subprocess.Popen([BIN,'--disable-audio'],stdout=subprocess.PIPE)
        for bline in facotrio_process.stdout:
            line=bline.decode().strip()
            if line.endswith("Factorio initialised"):
                facotrio_process.terminate()
        find_config()
        if not CONFIG:
            input("Configuration creation failed. Please report to Factorio Access Maintainers\nPress Enter to exit.")
            raise SystemExit
    else:
        raise SystemExit

if not os.path.isdir(WRITE_DIR):
    raise Exception("Unable to find factorio write directory")
if not os.path.isdir(READ_DIR):
    raise Exception("Unable to find factorio data directory")

MODS=os.path.join(WRITE_DIR,'mods') #todo customize according to args
SAVES=os.path.join(WRITE_DIR,'saves')
PLAYER_DATA = os.path.join(WRITE_DIR, "player-data.json")
TEMP = os.path.join(WRITE_DIR,  'temp')

MOD_NAME = "FactorioAccess"
__my_mod_folder = os.path.join(MY_BIN,'..','mods')
if os.path.isdir(__my_mod_folder) and not os.path.samefile(__my_mod_folder,MODS):
    __my_mod = os.path.join(__my_mod_folder,MOD_NAME)
    if os.path.exists(__my_mod):
        try:
            shutil.rmtree(os.path.join(MODS,MOD_NAME))
        except FileNotFoundError:
            pass
        shutil.move(__my_mod,MODS)
