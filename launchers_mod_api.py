import re
from pyperclip import copy
import accessible_output2.outputs.auto
import pyautogui as gui  # cSpell: ignore pyautogui

from fa_arg_parse import d_print
from translations import translate

gui.FAILSAFE = False
ao_output = accessible_output2.outputs.auto.Auto()


rich_text = re.compile(
    r"\[\/?(font|color|img|item|entity|technology|recipe|item-group|fluid|tile|virtual-signal|achievement|gps|special-item|armor|train|train-stop|tooltip)[^\]]*\]"
)
maybe_key = re.compile(r'(?<=[\s"]).(?=[\s"])')


def translate_key_name(m: re.Match):
    key = m[0]
    # exception needed for [ because localization cfg files can't use [ as a key since it indicates start of new section.
    if key == "[":
        key = "left-bracket"
    return translate(("?", ("control-keys." + key,), m[0]))



def speak_interruptable_text(text):
    text = rich_text.sub("", text)
    text = maybe_key.sub(translate_key_name, text)
    d_print(text)
    ao_output.output(text, interrupt=True)



def setCursor(coord_string):
    coords = [int(coord) for coord in coord_string.split(",")]
    gui.moveTo(coords[0], coords[1], _pause=False)





player_specific_commands = {
    "out": speak_interruptable_text,
    "setCursor": setCursor,
    "copy": copy,
}
global_commands = {
}