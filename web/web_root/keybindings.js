"use-strict";
(()=>{//clean global namespace
    let named_key_map={
        "Again":"AGAIN",
        "AltLeft":"LALT",
        "AltRight":"RALT",
        "ArrowDown":"DOWN",
        "ArrowLeft":"LEFT",
        "ArrowRight":"RIGHT",
        "ArrowUp":"UP",
        "AudioVolumeDown":"VOLUMEDOWN",
        "AudioVolumeMute":"AUDIOMUTE",
        "AudioVolumeUp":"VOLUMEUP",
        "Backquote":"GRAVE",
        "Backslash":"BACKSLASH",
        "Backspace":"BACKSPACE",
        "BracketLeft":"LEFTBRACKET",
        "BracketRight":"RIGHTBRACKET",
        "BrowserBack":"AC_BACK",
        "BrowserFavorites":"AC_BOOKMARKS",
        "BrowserForward":"AC_FORWARD",
        "BrowserHome":"AC_HOME",
        "BrowserRefresh":"AC_REFRESH",
        "BrowserSearch":"AC_SEARCH",
        "BrowserStop":"AC_STOP",
        "CapsLock":"CAPSLOCK",
        "Comma":"COMMA",
        "ContextMenu":"MENU",
        "ControlLeft":"LCTRL",
        "ControlRight":"RCTRL",
        "Copy":"COPY",
        "Cut":"CUT",
        "Delete":"DELETE",
        "Digit0":"0",
        "Digit1":"1",
        "Digit2":"2",
        "Digit3":"3",
        "Digit4":"4",
        "Digit5":"5",
        "Digit6":"6",
        "Digit7":"7",
        "Digit8":"8",
        "Digit9":"9",
        "Eject":"EJECT",
        "End":"END",
        "Enter":"RETURN",
        "Equal":"EQUALS",
        "Escape":"ESCAPE",
        "F1":"F1",
        "F10":"F10",
        "F11":"F11",
        "F12":"F12",
        "F13":"F13",
        "F14":"F14",
        "F15":"F15",
        "F16":"F16",
        "F17":"F17",
        "F18":"F18",
        "F19":"F19",
        "F2":"F2",
        "F20":"F20",
        "F21":"F21",
        "F22":"F22",
        "F23":"F23",
        "F24":"F24",
        "F3":"F3",
        "F4":"F4",
        "F5":"F5",
        "F6":"F6",
        "F7":"F7",
        "F8":"F8",
        "F9":"F9",
        "Find":"FIND",
        "Help":"HELP",
        "Home":"HOME",
        "Insert":"INSERT",
        "IntlBackslash":"NONUSBACKSLASH",
        "KeyA":"A",
        "KeyB":"B",
        "KeyC":"C",
        "KeyD":"D",
        "KeyE":"E",
        "KeyF":"F",
        "KeyG":"G",
        "KeyH":"H",
        "KeyI":"I",
        "KeyJ":"J",
        "KeyK":"K",
        "KeyL":"L",
        "KeyM":"M",
        "KeyN":"N",
        "KeyO":"O",
        "KeyP":"P",
        "KeyQ":"Q",
        "KeyR":"R",
        "KeyS":"S",
        "KeyT":"T",
        "KeyU":"U",
        "KeyV":"V",
        "KeyW":"W",
        "KeyX":"X",
        "KeyY":"Y",
        "KeyZ":"Z",
        "Lang1":"LANG1",
        "Lang2":"LANG2",
        "Lang3":"LANG3",
        "Lang4":"LANG4",
        "Lang5":"LANG5",
        "LaunchApp1":"APP1",
        "LaunchApp2":"APP2",
        "LaunchMail":"MAIL",
        "MediaPlayPause":"AUDIOPLAY",
        "MediaSelect":"MEDIASELECT",
        "MediaStop":"AUDIOSTOP",
        "MediaTrackNext":"AUDIONEXT",
        "MediaTrackPrevious":"AUDIOPREV",
        "MetaLeft":"LGUI",
        "MetaRight":"RGUI",
        "Minus":"MINUS",
        "NumLock":"NUMLOCKCLEAR",
        "Numpad0":"KP_0",
        "Numpad1":"KP_1",
        "Numpad2":"KP_2",
        "Numpad3":"KP_3",
        "Numpad4":"KP_4",
        "Numpad5":"KP_5",
        "Numpad6":"KP_6",
        "Numpad7":"KP_7",
        "Numpad8":"KP_8",
        "Numpad9":"KP_9",
        "NumpadAdd":"KP_PLUS",
        "NumpadComma":"KP_COMMA",
        "NumpadDecimal":"KP_PERIOD",
        "NumpadDivide":"KP_DIVIDE",
        "NumpadEnter":"KP_ENTER",
        "NumpadEqual":"KP_EQUALS",
        "NumpadMultiply":"KP_MULTIPLY",
        "NumpadParenLeft":"KP_LEFTPAREN",
        "NumpadParenRight":"KP_RIGHTPAREN",
        "NumpadSubtract":"KP_MINUS",
        "PageDown":"PAGEDOWN",
        "PageUp":"PAGEUP",
        "Paste":"PASTE",
        "Pause":"PAUSE",
        "Period":"PERIOD",
        "Power":"POWER",
        "PrintScreen":"PRINTSCREEN",
        "Quote":"APOSTROPHE",
        "ScrollLock":"SCROLLLOCK",
        "Select":"SELECT",
        "Semicolon":"SEMICOLON",
        "ShiftLeft":"LSHIFT",
        "ShiftRight":"RSHIFT",
        "Slash":"SLASH",
        "Sleep":"SLEEP",
        "Space":"SPACE",
        "Tab":"TAB",
        "Undo":"UNDO",

    }
    
    function get_display_text_from_factorio_key(f_key){

    }
    let event_ops={
    }
    function captured_input(event){
        event.preventDefault()
        console.log(event)
        window.removeEventListener('mousedown',captured_input,event_ops)
        window.removeEventListener('keydown',captured_input,event_ops)
    }
    let button=null
    function capture_input(event){
        button=event.target
        window.addEventListener('mousedown',captured_input,event_ops)
        window.addEventListener('keydown',captured_input,event_ops)
    }
    document.getElementById('keybindings').addEventListener('click',capture_input)
})()