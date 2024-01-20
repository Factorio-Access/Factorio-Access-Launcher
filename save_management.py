import time
import os

from fa_paths import SAVES
from fa_menu import getAffirmation

def get_elapsed_time(t1):
    t2 = time.time()
    days = (t2-t1)/60/60/24
    if days >= 1:
        return str(int(days)) + " days"
    hours = (t2-t1)/60/60
    if hours >= 1:
        return str(int(hours)) + " hours"
    minutes = (t2-t1)/60
    if minutes >= 1:
        return str(int(minutes)) + " minutes"
    return str(int(t2-t1+0.999)) + " seconds"


def save_time(file):
    return os.path.getmtime(os.path.join(SAVES,file))

def get_sorted_saves():
    try:
        l = os.listdir(SAVES)
        l.sort(reverse=True, key=save_time)
        return l
    except:
        return []

def get_menu_saved_games():
    games = get_sorted_saves()
    return {save[:-4] + " " + get_elapsed_time(save_time(save)) + " ago" : save for save in games}


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
                    dst = os.path.join(SAVES, newName + ".zip")
                    testFile = open(dst, "w")
                    testFile.close()
                    os.remove(dst)
                    check = True
                except:
                    print("Invalid file name, please try again.")
            src = os.path.join(SAVES,save)
            os.replace(src, dst)
            print("Renamed.")
            return
    print("Looks like you didn't save!")
