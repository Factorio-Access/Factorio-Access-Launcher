import json
import re
import os
from contextlib import ExitStack
from pyperclip import copy
import accessible_output2.outputs.auto


from fa_arg_parse import d_print
from fa_launcher_audio import AudioManager
from translations import translate
from mods import mods, dual_path

wayland = os.environ.get("XDG_SESSION_TYPE", "") == "wayland"
if not wayland:
    import pyautogui as gui  # cSpell: ignore pyautogui

    gui.FAILSAFE = False
ao_output = accessible_output2.outputs.auto.Auto()

# Audio session management
_audio_exit_stack: ExitStack | None = None
audio_manager: AudioManager | None = None
audio_path: dual_path | None = None
FA_MOD_FILTER = re.compile(r"FactorioAccess")


def audio_data_provider(name: str) -> bytes:
    if not audio_path:
        raise RuntimeError(f"No audio path when loading audio: {name}")
    path = audio_path
    for part in name.replace("\\", "/").split("/"):
        path = path / part
    return path.read_bytes()


def start_audio_session():
    global _audio_exit_stack, audio_manager, audio_path

    with mods as m:
        audio_path = m.get_current_mod_path("FactorioAccess") / "audio"
    _audio_exit_stack = ExitStack()
    audio_manager = _audio_exit_stack.enter_context(
        AudioManager(data_provider=audio_data_provider)
    )


def stop_audio_session():
    global _audio_exit_stack, audio_manager, audio_path
    if _audio_exit_stack:
        _audio_exit_stack.close()
        _audio_exit_stack = None
        audio_manager = None
        audio_path = None


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
    if not wayland:
        coords = [int(coord) for coord in coord_string.split(",")]
        gui.moveTo(coords[0], coords[1], _pause=False)


def handle_acmd(json_string: str):
    if not audio_manager:
        d_print("acmd: no audio session active")
        return
    try:
        command = json.loads(json_string)
        audio_manager.submit_command(command)
    except json.JSONDecodeError as e:
        d_print(f"acmd: invalid JSON: {e}")


player_specific_commands = {
    "out": speak_interruptable_text,
    "setCursor": setCursor,
    "copy": copy,
    "acmd": handle_acmd,
}
global_commands = {}
