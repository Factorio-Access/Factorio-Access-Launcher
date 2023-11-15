#!/usr/bin/env python3
import pyautogui as gui
import time
import math
import os
import sys
import subprocess
import threading
import json
import shutil
import re

import accessible_output2.outputs.auto

import fa_paths
import update_factorio
import multiplayer
import fa_menu
from fa_menu import *
import modify_config

ao_output = accessible_output2.outputs.auto.Auto()

gui.FAILSAFE = False

if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
    fa_paths.BIN=sys.argv[1]


ao_output.output("Hello Factorio!", False)



def get_elapsed_time(t1):
    t2 = time.time()
    days = (t2-t1)/60/60/24
    if days >= 1:
        return str(math.floor(days)) + " days"
    hours = (t2-t1)/60/60
    if hours >= 1:
        return str(math.floor(hours)) + " hours"
    minutes = (t2-t1)/60
    if minutes >= 1:
        return str(math.floor(minutes)) + " minutes"
    return str(math.ceil(t2-t1)) + " seconds"


def save_time(file):
    return os.path.getmtime(os.path.join(fa_paths.SAVES,file))

def get_sorted_saves():
    try:
        l = os.listdir(fa_paths.SAVES)
        l.sort(reverse=True, key=save_time)
        return l
    except:
        return []

def get_menu_saved_games():
    games = get_sorted_saves()
    return {save[:-4] + " " + get_elapsed_time(save_time(save)) + " ago" : save for save in games}



def customMapSettings():
    print("Please enter a name for your new settings file:\n")
    i = input()
    result = i
    path = "Map Settings/Custom Settings/" + i
    if not os.path.exists(path):
        os.makedirs(path)
    with open(os.path.join(path, "MapGenSettings.json"), 'w') as fp:
        fp.write(
            """{\n  "_terrain_segmentation_comment": "The inverse of 'water scale' in the map generator GUI.",\n""")
        print("Enter a value for terrain segmentation.  \nIt represents the size of biomes, where 1.0 is default, 2.0 is twice as large .5 is half as large, et cetera.")
        i = getNum()
        fp.write('  "terrain_segmentation": ' + i + ',\n\n')
        fp.write("""  "_water_comment":
  [
    "The equivalent to 'water coverage' in the map generator GUI. Higher coverage means more water in larger oceans.",
    "Water level = 10 * log2(this value)"
  ],
""")
        print("Enter the value for water level.\nHigher values lead to larger and more frequentt oceans.\nThe default value is 1.0")
        i = getNum()
        fp.write('  "water": ' + i + ',\n\n')
        print(
            "Enter the maximum width of the map in tiles,\n0 is both infinite and default.")
        i = getNum()
        fp.write('  "width": ' + i + ',\n')
        print(
            "Enter the maximum height of the map in tiles,\n0 is both infinite and default.")
        i = getNum()
        fp.write('  "height": ' + i + ',\n\n')
        fp.write("""  "_starting_area_comment": "Multiplier for 'biter free zone radius'",
""")
        print("Enter a multiplier for the size of your starting zone.\nAgain, 2 would be 200%, 1 is 100% and default, and .5 is 50%")
        i = getNum()
        fp.write('  "starting_area": ' + i + ',\n')
        print("Enter either true or false, to indicate whether enemies are docile until attacked.  Default is false\n")
        i = getBoolean()
        fp.write('  "peaceful_mode": ' + i + ',\n\n')
        fp.write("""  "autoplace_controls":
  {
""")
        print("Enter the frequency of coal.  The default value is 1.0, and this value determines how often coal is encountered on the map.")
        i = getNum()
        print("Enter the size of coal.  The default value is 1.0, and this value determines how large a deposit of coal is when found on the map.")
        i1 = getNum()
        print("Enter the richness of coal.  The default value is 1.0, and this value determines how much coal is on a single tile when found on the map.")
        i2 = getNum()
        fp.write('    "coal": {"frequency": ' + i +
                 ', "size": ' + i1 + ', "richness": ' + i2 + '},\n')

        print("Enter the frequency of stone.The default value is 1.0, and this value determines how often stone is encountered on the map.")
        i = getNum()
        print("Enter the size of stone.  The default value is 1.0, and this value determines how large a deposit of stone is when found on the map.")
        i1 = getNum()
        print("Enter the richness of stone.  The default value is 1.0, and this value determines how much stone is on a single tile when found on the map.")
        i2 = getNum()
        fp.write('    "stone": {"frequency": ' + i +
                 ', "size": ' + i1 + ', "richness": ' + i2 + '},\n')

        print("Enter the frequency of copper.  The default value is 1.0, and this value determines how often copper is encountered on the map.")
        i = getNum()
        print("Enter the size of copper.  The default value is 1.0, and this value determines how large a deposit of copper is when found on the map.")
        i1 = getNum()
        print("Enter the richness of copper.  The default value is 1.0, and this value determines how much copper is on a single tile when found on the map.")
        i2 = getNum()
        fp.write('    "copper-ore": {"frequency": ' + i +
                 ', "size": ' + i1 + ', "richness": ' + i2 + '},\n')

        print("Enter the frequency of iron.  The default value is 1.0, and this value determines how often iron is encountered on the map.")
        i = getNum()
        print("Enter the size of iron.  The default value is 1.0, and this value determines how large a deposit of iron is when found on the map.")
        i1 = getNum()
        print("Enter the richness of iron.  The default value is 1.0, and this value determines how much iron is on a single tile when found on the map.")
        i2 = getNum()
        fp.write('    "iron-ore": {"frequency": ' + i +
                 ', "size": ' + i1 + ', "richness": ' + i2 + '},\n')

        print("Enter the frequency of uranium.  The default value is 1.0, and this value determines how often uranium is encountered on the map.")
        i = getNum()
        print("Enter the size of uranium.  The default value is 1.0, and this value determines how large a deposit of uranium is when found on the map.")
        i1 = getNum()
        print("Enter the richness of uranium.  The default value is 1.0, and this value determines how much uranium is on a single tile when found on the map.")
        i2 = getNum()
        fp.write('    "uranium-ore": {"frequency": ' + i +
                 ', "size": ' + i1 + ', "richness": ' + i2 + '},\n')

        print("Enter the frequency of oil.  The default value is 1.0, and this value determines how often oil is encountered on the map.")
        i = getNum()
        print("Enter the size of oil.  The default value is 1.0, and this value determines how large a deposit of oil is when found on the map.")
        i1 = getNum()
        print("Enter the richness of oil.  The default value is 1.0, and this value determines how much oil is on a single tile when found on the map.")
        i2 = getNum()
        fp.write('    "crude-oil": {"frequency": ' + i +
                 ', "size": ' + i1 + ', "richness": ' + i2 + '},\n')

        print("Enter the frequency of forests.  The default value is 1.0, and this value determines how often forests are encountered on the map.")
        i = getNum()
        print("Enter the size of forests.  The default value is 1.0, and this value determines how large a forest is when found on the map.")
        i1 = getNum()
        print("Enter the richness of forests.  The default value is 1.0, and this value determines how healthy forests are when found on the map.")
        i2 = getNum()
        fp.write('    "trees": {"frequency": ' + i +
                 ', "size": ' + i1 + ', "richness": ' + i2 + '},\n')

        print("Enter the frequency of enemy bases.  The default value is 1.0, and this value determines how often bases are encountered on the map.")
        i = getNum()
        print("Enter the size of enemy bases.  The default value is 1.0, and this value determines how large an enemy base is when found on the map.")
        i1 = getNum()
        print("Enter the density of enemy bases.  The default value is 1.0, and this value determines how many enemy buildings are in a single base when found on the map.")
        i2 = getNum()
        fp.write('    "enemy-base": {"frequency": ' + i +
                 ', "size": ' + i1 + ', "richness": ' + i2 + '}\n')

        fp.write("""  },

  "cliff_settings":
  {
    "_name_comment": "Name of the cliff prototype",
    "name": "cliff",

    "_cliff_elevation_0_comment": "Elevation of first row of cliffs",
""")

        print("Enter the elevation of the first row of any cliff.  As far as I can tell, this only has a visual effect, but the default is 10 if you want to play around with it.")
        i = getNum()
        fp.write('    "cliff_elevation_0": ' + i + ',\n\n')
        fp.write("""    "_cliff_elevation_interval_comment":
    [
      "Elevation difference between successive rows of cliffs.",
      "This is inversely proportional to 'frequency' in the map generation GUI. Specifically, when set from the GUI the value is 40 / frequency."
    ],
""")
        print("Enter the average distance between cliffs.  The default value is 40, so if you want twice as many cliffs enter 20 or half as many cliffs enter 80.")
        i = getNum()
        fp.write('    "cliff_elevation_interval": '+i+',\n')
        print("Enter cliff density.  The default value is 1, and it determines how porous cliffs are.  a value of 10 will cause there to be no breaks in the cliffs, while a value of 0 will not spawn any cliffs at all IE completely porous.")
        i = getNum()
        fp.write('    "richness": ' + i + '\n')
        fp.write("""  },

  "_property_expression_names_comment":
  [
    "Overrides for property value generators (map type)",
    "Leave 'elevation' blank to get 'normal' terrain.",
    "Use 'elevation': '0_16-elevation' to reproduce terrain from 0.16.",
    "Use 'elevation': '0_17-island' to get an island.",
    "Moisture and terrain type are also controlled via this.",
    "'control-setting:moisture:frequency:multiplier' is the inverse of the 'moisture scale' in the map generator GUI.",
    "'control-setting:moisture:bias' is the 'moisture bias' in the map generator GUI.",
    "'control-setting:aux:frequency:multiplier' is the inverse of the 'terrain type scale' in the map generator GUI.",
    "'control-setting:aux:bias' is the 'terrain type bias' in the map generator GUI."
  ],
  "property_expression_names":
  {
""")
        print("Do you want to select an island map?  This will mean that beyond a certain distance from your starting zone, the map is an endless ocean.\nPlease enter either yes or no.  No is the default.")
        if (getAffirmation()):
            fp.write('    "elevation": "0_17-island",\n')
        print("Enter the value for moisture frequency.")
        i = getNum()
        fp.write(
            '    "control-setting:moisture:frequency:multiplier": "' + i + '",\n')
        print("Enter the value for moisture bias")
        i = getNum()
        fp.write('    "control-setting:moisture:bias": "' + i + '",\n')
        print("Enter value for terrain generation type.")
        i = getNum()
        fp.write('    "control-setting:aux:frequency:multiplier": "'+i+'",\n')
        print("Enter value for terrain bias.")
        i = getNum()
        fp.write('    "control-setting:aux:bias": "'+i+'"\n')
        fp.write("""  },

  "starting_points":
  [
""")
        print("Enter the x coordinate position that you would like to start the game at.")
        i = getNum()
        print("Enter the y coordinate position you would like to start the game at.")
        i1 = getNum()
        fp.write('    { "x": '+i+', "y": '+i1+'}\n')
        fp.write("""  ],

  "_seed_comment": "Use null for a random seed, number for a specific seed.",
""")
        print("Would you like to provide a seed for the random number generator?Please enter yes or no.")
        if getAffirmation():
            print("Enter the value of your seed, results must be positive integers.")
            i = getNum()
        else:
            i = 'null'
        fp.write('  "seed": ' + i + '\n')
        fp.write("}\n")

    shutil.copyfile("Map Settings/PeacefulSettings.json", os.path.join(path, "mapSettings.json"))
    return result


def customMapList():
    command = -1
    name = ""
    while not name:
        print("Select custom settings:\n")
        print("0 : Create new settings")
        try:
            l = os.listdir("Map Settings/Custom Settings")
        except:
            l = []
        for i in range(len(l)):
            print(i+1, ": ", l[i])
        i = input()
        try:
            int(i)
        except:
            print("Invalid Command\n")
            continue
        if int(i) == 0:
            name = customMapSettings()
        for k in range(len(l)):
            if int(i) == k+1:
                name = l[k]
                break
    path = os.path.join("Map Settings/Custom Settings/", name)
    create_new_save(os.path.join(path,"mapSettings.json"),os.path.join(path,"mapGenSettings.json"))

def speak_interuptible_text(text):
    ao_output.output(text,True)
def setCursor(coordstring):
    coords = [int(coord) for coord in coordstring.split(",")]
    gui.moveTo(coords[0], coords[1], _pause=False)

player_list={}
def set_player_list(jsons):
    global player_list
    player_list = {key[1:]:val for key,val in json.loads(jsons).items()}

player_specific_commands = {
    "out":speak_interuptible_text,
    "setCursor":setCursor,
    }
global_commands = {
    "playerList":set_player_list,
    }

def get_updated_presets():
    print("Getting Available Settings")
    #launch_with_params(["--dump-data"])
    data=json.load(open(os.path.join(fa_paths.WRITE_DIR,'script-output','data-raw-dump.json')))
    for preset_group in data['map-gen-presets'].values():
        for preset_name,preset in preset_group.items():
            if preset_name=='type' or preset_name=='name':
                continue
            print(preset_name,len(preset))
    pass

def process_game_stdout(stdout,announce_press_e):
    player_index=""
    restarting=False
    for bline in iter(stdout.readline, b''):
        if fa_menu.debug:
            print(bline)
        line:str = bline.decode('utf-8').rstrip('\r\n')
        parts = line.split(' ',1)
        if len(parts)==2:
            if parts[0] in player_specific_commands:
                more_parts = parts[1].split(" ",1)
                if not player_index or more_parts[0] == player_index:
                    player_specific_commands[parts[0]](more_parts[1])
                    continue
            elif parts[0] in global_commands:
                global_commands[parts[0]](parts[1])
                continue
               
        if line.endswith("Saving finished"):
            ao_output.output("Saving Complete", True)
        elif line.endswith("time start"):
            debug_time = time.time
        elif line.endswith("time end"):
            print(time.time - debug_time)
        elif line.endswith("Restarting Factorio"):
            restarting=True
        elif line.endswith("Goodbye"):
            if not restarting:
                pass#return
            restarting=False
        elif m:=re.search(r'PlayerJoinGame .*?playerIndex\((\d+)\)',line):
            if not player_index:
                player_index=str(int(m[1])+1)
                print(f'Player index now {player_index}')
        elif re.search(r'Quitting multiplayer connection.',line):
            player_index=""
            print(f'Player index cleared')
        elif announce_press_e and line.endswith("Factorio initialised"):
            announce_press_e = False
            ao_output.output("Press e to continue", True)

def save_game_rename(if_after=None):
    l = get_sorted_saves()
    if len(l) > 0:
        save=l[0]
        save_t=save_time(save)
        if if_after and save_t > if_after:
            print("Would you like to name your last save?  You saved " +
                get_elapsed_time(save_t) + " ago")
            if not getAffirmation():
                return
            print("Enter a name for your save file:")
            check = False
            while check == False:
                newName = input()
                try:
                    dst = os.path.join(fa_paths.SAVES, newName + ".zip")
                    testFile = open(dst, "w")
                    testFile.close()
                    os.remove(dst)
                    check = True
                except:
                    print("Invalid file name, please try again.")
            src = os.path.join(fa_paths.SAVES,save)
            os.replace(src, dst)
            print("Renamed.")
            return
    print("Looks like you didn't save!")


def just_launch():
    launch_with_params([],announce_press_e=True)
    return 5

def connect_to_address_menu():
    address = input("Enter the address to connect to:\n")
    return connect_to_address(address)
def connect_to_address(address):
    return launch_with_params(["--mp-connect",address])

def create_new_save(map_setting,map_gen_setting):
    launch_with_params(["--map-gen-settings", map_gen_setting, "--map-settings",map_setting,'--create','saves/_autosave-manual.zip'],save_rename=False)

def launch(path):
    return launch_with_params(["--load-game", path])
def launch_with_params(params,announce_press_e=False,save_rename=True):
    start_time=time.time()
    params = [
        fa_paths.BIN, 
        "--config", fa_paths.CONFIG,
        "--mod-directory", fa_paths.MODS,
        "--fullscreen", "TRUE"] + params
    try:
        print("Launching")
        proc = subprocess.Popen(params , stdout=subprocess.PIPE)
        threading.Thread(target=process_game_stdout, args=(proc.stdout,announce_press_e), daemon=True).start()
        proc.wait()
    except Exception as e:
        print("error running game")
        raise e
    if save_rename:
        save_game_rename(start_time)
    return 5
    


def chooseDifficulty():
    command = 0
    types={
        "Compass Valley":"CompassValleySettings.json",
        "Peaceful":"PeacefulSettings.json",
        "Easy":"PeacefulSettings.json",
        "Normal":"PeacefulSettings.json",
        "Hard":"PeacefulSettings.json",
        "Custom":False,
    }
    opts = ["Back"] + list(types)
    opt = select_option(opts,"Select type of map:",False)
    if opt == 0:
        return 0
    key = opts[opt]
    if types[key]:
        create_new_save("Map Settings/"+types[key],f"Map Settings/gen/{key.replace(' ','')}Map.json")
    else:
        customMapList()
    return launch("saves/_autosave-manual.zip")
    
def time_to_exit():
    ao_output.output("Goodbye Factorio", False)
    time.sleep(1)
    sys.exit(0)
    
menu = {
    "Launch last played":just_launch,
    "Single Player":{
        "New Game" : chooseDifficulty,
        "Load Game" : {
            get_menu_saved_games:launch,
            },
        },
    "Multiplayer":{
        multiplayer.get_username_menu:multiplayer.username_menu,
        "Host Settings":{
            multiplayer.get_host_settings_menu:multiplayer.run_func
        },
        "Host Saved Game": {
            get_menu_saved_games: multiplayer.multiplayer_launch,
            },
        "Browse Public":{
            "Freind List":{
                "Add":multiplayer.add_friend_menu,
                 multiplayer.get_friends_menu: multiplayer.specific_friend_menu
            },
            "List Games With Friends":{
                multiplayer.games_with_friends_menu: connect_to_address
            }
        },
        "Connect to Address": connect_to_address_menu,
        },
    "Quit": time_to_exit,
    }

modify_config.do_config_check()
do_menu(menu,"Main Menu",False)