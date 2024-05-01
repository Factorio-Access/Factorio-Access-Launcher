
import fa_menu
import config

check_cats={
   "multiplayer-lobby":["gui-multiplayer-lobby","config-help"],
   "map-view":["gui-map-view-settings"],
   "controls":["controls"],
   "input":["gui-control-settings"],
   "controller":["gui-control-settings"],
   "graphics":["gui-graphics-settings"],
   "interface":["gui-interface-settings"],
   "other":["gui-other-settings"],
   "sound":["gui-sound-settings"],
   "general":["gui-interface-settings"]
}

setting_menu={
   ('gui-interface-settings.locale',):lambda :0,
   ('gui-menu.graphics',):{
      ('gui-graphics-settings.general',):{},
      ('gui-graphics-settings.advanced',):{},
   },
   ('gui-menu.controls',):{},
   ('gui-menu.sound',):{},
   ('gui-menu.interface',):{},
   ('gui-menu.other',):{},
   ('gui-menu.mod-settings',):{},
}