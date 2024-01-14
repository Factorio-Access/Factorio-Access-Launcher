import json
from typing import Any, Callable
import weakref

import fa_paths
import os
import fa_menu
from translations import localised_str

ore_type=0

menu={
    ("gui-map-generator.resources-tab-title",):{
        ore_type:{
            "frequency":0,
            "size":0,
            "richness":0
        }
    },
    ("gui-map-generator.terrain-tab-title",):{
        "Maptype":'''type = "noise-expression",
            name = "straight-basis-noise",
            intended_property = "elevation",''',
        "Water":{
            "Enabled":0,
            "Scale":0,
            "Coverage":0
        },
        "Trees":{
            "Enabled":0,
            "Scale":0,
            "Coverage":0
        },
        "Cliffs":{
            "Enabled":0,
            "Frequency":0,
            "Conitnuity":0
        },
        "Moisture":{
            "Scale":0,
            "Bias":0,
        },
        "Terain type":{
            "Scale":0,
            "Bias":0,
        }
    },
    ("gui-map-generator.enemy-tab-title",):{
        "Enemy bases":{
            "Frequency":0,
            "Size":0
        },
        "Peaceful mode":0,
        "Starting area size":0,
        "Enemy Expansion":{
            "Enabled":0,
            "Maximum expanstion distance":0,
            "Minimum group size":0,
            "Maximum group size":0,
            "Minimum cooldown":0,
            "Maximum cooldown":0,
        },
        "Evolution":{
            "Enabled":0,
            "Time factor":0,
            "Destroy factor":0,
            "Pollution factor":0
        }
    },
    ("gui-map-generator.advanced-tab-title",):{
        "Record replay information":0,
        "Map":{
            "Width":0,
            "Height":0,
        },
        "Recipes":{
            "Difficulty":0,
        },
        "Technology":{
            "Difficulty":0,
            "Price multiplier":0,
        },
        "Pollution":{
            "Enabled":0,
            "Absorption modifier":0,
            "Attack cost modifier":0,
            "Minimum to damage trees":0,
            "Absorbed per damaged tree":0,
            "Diffusion ratio":0,
        }
    }
}

class autoplace_enable_disable_menu(fa_menu.menu_item):
    def __init__(self, name: localised_str | Callable[..., Any] | dict, submenu, add_back=True) -> None:
        super().__init__(name, submenu, add_back)
        self.full_submenu=self.submenu
        self.remake_submenu()
    def get_menu_name(self):
        return ("",self.name,": ",self.submenu[0].val_to_string())
    def remake_submenu(self):
        if self.submenu[0].val:
            self.submenu=self.full_submenu
        else:
            self.submenu=[self.submenu[0]]

class autoplace_enable_disable_submenu(fa_menu.setting_menu_bool):
    def input_to_val(self, inp: str):
        super().input_to_val(inp)
        parent=self.parent()
        if not self.val:
            for sub in parent.submenu:
                if sub==self:
                    continue
                sub.val=0
        parent.remake_submenu()

class menu_setting_inverse_float(fa_menu.setting_menu_float):
    def val_to_string(self):
        return str(1.0/self.val)
    def input_to_val(self, inp: str):
        self.val = 1.0/float(inp)

#terrain based controls:
# frequency = 1/scale
# size      = coverage

# control-setting:x:frequency:multiplier = 1/scale
# control-setting:x:bias = bias

# cliff settings: 
# cliff_elevation_interval = 40 / frequency
# richness = continuity

data=json.load(open(os.path.join(fa_paths.WRITE_DIR,'script-output','data-raw-dump.json')))
for preset_group in data['map-gen-presets'].values():
    for preset_name,preset in preset_group.items():
        if preset_name=='type' or preset_name=='name':
            continue
        print(preset_name,len(preset))
for name,preset_group in data['noise-layer'].items():
    print(name,preset_group)

category_mapping={
    'resource':,
    'terrain':menu[("gui-map-generator.terrain-tab-title",)],
    'enemy':menu[("gui-map-generator.enemy-tab-title",)]
}

for name,control in data['autoplace-control'].items():
    submenu={}
    if 'can_be_disabled' not in control or control['can_be_disabled']:
        submenu['en/disable']=autoplace_enable_disable_submenu()
    
    name= control['localised_name'] if 'localised_name' in control else ('autoplace-control-names.'+control['name'],)
    if control['category'] == 'resource':
        parent=menu[("gui-map-generator.resources-tab-title",)]
        submenu['frequency']=fa_menu.setting_menu_float(("gui-map-generator.frequency",),("gui-map-generator.resource-frequency-description",),1,1)
        submenu['size']=fa_menu.setting_menu_float(("gui-map-generator.size",),("gui-map-generator.resource-size-description",),1,1)
        if 'richness' in control and control['richness']:
            submenu['richness']=fa_menu.setting_menu_float(("gui-map-generator.richness",),("gui-map-generator.resource-richness-description",),1,1)
        name=('entity-name.'+control.name,)
    elif control['category'] == 'terrain':
        parent=menu[("gui-map-generator.terrain-tab-title",)]
        submenu['frequency']=menu_setting_inverse_float(("gui-map-generator.scale",),("gui-map-generator.terrain-scale-description",),1,1)
        submenu['size']=fa_menu.setting_menu_float(("gui-map-generator.coverage",),("gui-map-generator.terrain-coverage-description",),1,1)
    else:
        parent=menu[("gui-map-generator.enemy-tab-title",)]
        submenu['frequency']=fa_menu.setting_menu_float(("gui-map-generator.frequency",),("gui-map-generator.enemy-frequency-description",),1,1)
        submenu['size']=fa_menu.setting_menu_float(("gui-map-generator.size",),("gui-map-generator.enemy-size-description",),1,1)
    my_menu = autoplace_enable_disable_menu(name,submenu)
    if 'en/disable' in submenu:
        submenu['en/disable'].parent=weakref.ref(my_menu)
    print(name,preset_group)
    print()

class SettingEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, fa_menu.menu_item):
            return obj.val
        # Let the base class default method raise the TypeError
        return super().default(obj)



map_gen_settings_json={
  "_terrain_segmentation_comment": "The inverse of 'water scale' in the map generator GUI.",
  "terrain_segmentation": 1,

  "_water_comment":
  [
    "The equivalent to 'water coverage' in the map generator GUI. Higher coverage means more water in larger oceans.",
    "Water level = 10 * log2(this value)"
  ],
  "water": 1,

  "_comment_width+height": "Width and height of map, in tiles; 0 means infinite",
  "width": 0,
  "height": 0,

  "_starting_area_comment": "Multiplier for 'biter free zone radius'",
  "starting_area": 1,

  "peaceful_mode": False,
  "autoplace_controls":
  {
    "coal": {"frequency": 1, "size": 1, "richness": 1},
    "stone": {"frequency": 1, "size": 1, "richness": 1},
    "copper-ore": {"frequency": 1, "size": 1,"richness": 1},
    "iron-ore": {"frequency": 1, "size": 1, "richness": 1},
    "uranium-ore": {"frequency": 1, "size": 1, "richness": 1},
    "crude-oil": {"frequency": 1, "size": 1, "richness": 1},
    "trees": {"frequency": 1, "size": 1, "richness": 1},
    "enemy-base": {"frequency": 1, "size": 1, "richness": 1}
  },

  "cliff_settings":
  {
    "_name_comment": "Name of the cliff prototype",
    "name": "cliff",

    "_cliff_elevation_0_comment": "Elevation of first row of cliffs",
    "cliff_elevation_0": 10,

    "_cliff_elevation_interval_comment":
    [
      "Elevation difference between successive rows of cliffs.",
      "This is inversely proportional to 'frequency' in the map generation GUI. Specifically, when set from the GUI the value is 40 / frequency."
    ],
    "cliff_elevation_interval": 40,

    "_richness_comment": "Called 'cliff continuity' in the map generator GUI. 0 will result in no cliffs, 10 will make all cliff rows completely solid",
    "richness": 1
  },

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
    "control-setting:moisture:frequency:multiplier": "1",
    "control-setting:moisture:bias": "0",
    "control-setting:aux:frequency:multiplier": "1",
    "control-setting:aux:bias": "0"
  },

  "_seed_comment": "Use null for a random seed, number for a specific seed.",
  "seed": None
}
