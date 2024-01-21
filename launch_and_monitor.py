import subprocess
import threading
import time
import json
import re
import os

import accessible_output2.outputs.auto
import pyautogui as gui

from fa_arg_parse import launch_args, args
from save_management import save_game_rename

gui.FAILSAFE = False

ao_output = accessible_output2.outputs.auto.Auto()
ao_output.output("Hello Factorio!", False)


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



def process_game_stdout(stdout,announce_press_e,tweak_modified):
    player_index=""
    restarting=False
    for bline in iter(stdout.readline, b''):
        if args.fa_debug:
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
        elif tweak_modified and "Loading map" in line:
            os.utime(tweak_modified[0],(tweak_modified[1],tweak_modified[1]))
            tweak_modified=None
        elif announce_press_e and line.endswith("Factorio initialised"):
            announce_press_e = False
            ao_output.output("Press e to continue", True)                
            

def just_launch():
    launch_with_params([],announce_press_e=True)
    return 5

def connect_to_address_menu():
    address = input("Enter the address to connect to:\n")
    return connect_to_address(address)
def connect_to_address(address):
    return launch_with_params(["--mp-connect",address])

def launch(path):
    return launch_with_params(["--load-game", path])
def launch_with_params(params,announce_press_e=False,save_rename=True,tweak_modified=None):
    start_time=time.time()
    if tweak_modified:
        old_time=os.path.getmtime(tweak_modified)
        os.utime(tweak_modified,(start_time,start_time))
        tweak_modified=(tweak_modified,old_time)
    params = launch_args + params
    try:
        print("Launching")
        proc = subprocess.Popen(params , stdout=subprocess.PIPE)
        threading.Thread(target=process_game_stdout, args=(proc.stdout,announce_press_e,tweak_modified), daemon=True).start()
        proc.wait()
    except Exception as e:
        print("error running game")
        raise e
    if save_rename:
        save_game_rename(start_time)
    return 5

def time_to_exit():
    ao_output.output("Goodbye Factorio", False)
    time.sleep(1.5)
    raise SystemExit