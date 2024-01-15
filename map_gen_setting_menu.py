import json
from typing import Any, Callable
import weakref

import fa_paths
import os
import fa_menu
from translations import localised_str


class autoplace_enable_disable_menu(fa_menu.menu_item):
    def __init__(self, name: localised_str | Callable[..., Any] | dict, submenu: dict, desc: localised_str | None = None) -> None:
        enabler=autoplace_enable_disable_submenu(("gui-map-generator.enabled",))
        enabler.parent=weakref.ref(self)
        my_submenu={'enabled':enabler}
        my_submenu.update(submenu)
        self.my_name=name
        super().__init__(self.name, my_submenu, desc, True)
        self.full_submenu=self.submenu
        self.remake_submenu()
    def name(self):
        return ("",self.my_name,": ",self.submenu[1].val_to_string())
    def get_menu_name(self):
        return self.my_name
    def remake_submenu(self):
        if self.submenu[1].val:
            self.submenu=self.full_submenu
        else:
            self.submenu=self.submenu[:2]

class autoplace_enable_disable_submenu(fa_menu.setting_menu_bool):
    def __call__(self):
        super().__call__()
        parent=self.parent()
        if not self.val:
            for sub in parent.submenu[2:]:
                sub.val=0
        parent.remake_submenu()
        return 0

class menu_setting_inverse_float(fa_menu.setting_menu_float):
    def val_to_string(self):
        if self.val==0:
            self.val=1.0
        return str(1.0/self.val)
    def input_to_val(self, inp: str):
        self.val = 1.0/float(inp)

class menu_setting_cliff_freq(fa_menu.setting_menu_float):
    def val_to_string(self):
        if self.val==0:
            self.val=1.0
        return str(40.0/self.val)
    def input_to_val(self, inp: str):
        self.val = 40.0/float(inp)

class menu_setting_evo(fa_menu.setting_menu_float):
    def val_to_string(self):
        return str(int(self.val*1e7+0.5))
    def input_to_val(self, inp: str):
        self.val = float(inp)*1e-7

class menu_setting_ticks_to_min(fa_menu.setting_menu_int):
    def val_to_string(self):
        return f"{self.val/3600:.2f}"
    def input_to_val(self, inp: str):
        self.val = int(float(inp)*3600)

data=json.load(open(os.path.join(fa_paths.WRITE_DIR,'script-output','data-raw-dump.json')))
for preset_group in data['map-gen-presets'].values():
    for preset_name,preset in preset_group.items():
        if preset_name=='type' or preset_name=='name':
            continue
        print(preset_name,len(preset))
for name,preset_group in data['noise-layer'].items():
    print(name,preset_group)

map_types={}
for name,exp in data['noise-expression'].items():
    if 'intended_property' in exp and exp['intended_property'] == "elevation":
        map_types[('noise-expression.'+name,)]=name


mgsj = { #Map Gen Settings Json file
  "terrain_segmentation": menu_setting_inverse_float(("gui-map-generator.scale",),("gui-map-generator.terrain-scale-description",)),
  "water": fa_menu.setting_menu_float(("gui-map-generator.coverage",),("gui-map-generator.terrain-coverage-description",)),

  "width": fa_menu.setting_menu_int(('gui-map-generator.map-width',)),
  "height": fa_menu.setting_menu_int(('gui-map-generator.map-height',)),

  "starting_area": fa_menu.setting_menu_float(('gui-map-generator.starting-area-size',),('gui-map-generator.starting-area-size-desciption',)),

  "peaceful_mode": fa_menu.setting_menu_bool(('gui-map-generator.peaceful-mode-checkbox',),('gui-map-generator.peaceful-mode-desciption',),False,False),
  "autoplace_controls":{},

  "cliff_settings":
  {
    "cliff_elevation_interval": menu_setting_cliff_freq(('gui-map-generator.cliff-frequency',),('gui-map-generator.cliff-frequency-desciption',),40,40),
    "richness": fa_menu.setting_menu_float(('gui-map-generator.cliff-continuity',),('gui-map-generator.cliff-continuity-desciption',))
  },

  "property_expression_names":
  {
    "elevation": fa_menu.setting_menu_options(('gui-map-generator.map-type',),map_types),
    "control-setting:moisture:frequency:multiplier": menu_setting_inverse_float(("gui-map-generator.scale",),("gui-map-generator.terrain-scale-description",)),
    "control-setting:moisture:bias": fa_menu.setting_menu_float(("gui-map-generator.bias",),("gui-map-generator.terrain-bias-description",),0,0),
    "control-setting:aux:frequency:multiplier": menu_setting_inverse_float(("gui-map-generator.scale",),("gui-map-generator.terrain-scale-description",)),
    "control-setting:aux:bias": fa_menu.setting_menu_float(("gui-map-generator.bias",),("gui-map-generator.terrain-bias-description",),0,0)
  },

  "seed": None
}

msj = { #Map Settings Json
  "difficulty_settings":
  {
    "recipe_difficulty": fa_menu.setting_menu_options(('gui-map-generator.difficulty',),{
                ('recipe-difficulty.normal',):0,
                ('recipe-difficulty.expensive',):1,                
            },None,0,0),
    "technology_difficulty": fa_menu.setting_menu_options(('gui-map-generator.difficulty',),{
                ('technology-difficulty.normal',):0,
                ('technology-difficulty.expensive',):1,                
            },None,0,0),
    "technology_price_multiplier": fa_menu.setting_menu_int(('gui-map-generator.price-multiplier',),None,1,1),
  },
  "pollution":
  {
    "enabled": None, #placeholder
    "diffusion_ratio": fa_menu.setting_menu_float(
                ('gui-map-generator.pollution-diffusion-ratio',),
                ('gui-map-generator.pollution-diffusion-ratio-description',),0.02,0.02),
    "ageing": fa_menu.setting_menu_float(
                ('gui-map-generator.pollution-absorption-modifier',),
                ('gui-map-generator.pollution-absorption-modifier-description',)),
    "min_pollution_to_damage_trees": fa_menu.setting_menu_int(
                ('gui-map-generator.minimum-pollution-to-damage-trees',),
                ('gui-map-generator.minimum-pollution-to-damage-trees-description',),60,60),
    "pollution_restored_per_tree_damage": fa_menu.setting_menu_int(
                ('gui-map-generator.pollution-absorbed-per-tree-damaged',),
                ('gui-map-generator.pollution-absorbed-per-tree-damaged-description',),10,10),
    "enemy_attack_pollution_consumption_modifier": fa_menu.setting_menu_float(
                ('gui-map-generator.enemy-attack-pollution-consumption-modifier',),
                ('gui-map-generator.enemy-attack-pollution-consumption-modifier-description',))
  },
  "enemy_evolution":
  {
    "enabled": None,#placeholder
    "time_factor": menu_setting_evo(('gui-map-generator.evolution-time-factor',),
                ('gui-map-generator.evolution-time-factor-description',),0.000004,0.000004),
    "destroy_factor": menu_setting_evo(('gui-map-generator.evolution-destroy-factor',),
                ('gui-map-generator.evolution-destroy-factor-description',),0.002,0.002),
    "pollution_factor": menu_setting_evo(('gui-map-generator.evolution-pollution-factor',),
                ('gui-map-generator.evolution-pollution-factor-description',),0.0000009,0.0000009)
  },
  "enemy_expansion":
  {
    "enabled": None, #placeholder
    "max_expansion_distance": fa_menu.setting_menu_int(
        ('enemy-expansion-maximum-expansion-distance',),
        ('enemy-expansion-maximum-expansion-distance-description',), 7,7),
    "settler_group_min_size": fa_menu.setting_menu_int(
        ('enemy-expansion-minimum-expansion-group-size',),
        ('enemy-expansion-minimum-expansion-group-size-description',), 5,5),
    "settler_group_max_size": fa_menu.setting_menu_int(
        ('enemy-expansion-maximum-expansion-group-size',),
        ('enemy-expansion-maximum-expansion-group-size-description',), 20,20),
    "min_expansion_cooldown": menu_setting_ticks_to_min(
        ('enemy-expansion-minimum-expansion-cooldown',),
        ('enemy-expansion-minimum-expansion-cooldown-description',), 14400,14400),
    "max_expansion_cooldown": menu_setting_ticks_to_min(
        ('enemy-expansion-maximum-expansion-cooldown',),
        ('enemy-expansion-maximum-expansion-cooldown-description',), 216000,216000)
  },
}


menu={
    ("gui-map-generator.resources-tab-title",):{},
    ("gui-map-generator.terrain-tab-title",):{
        "map_type":mgsj["property_expression_names"]["elevation"],
        "Water":autoplace_enable_disable_menu(
            ('gui-map-generator.water',),{
            "Scale":mgsj["terrain_segmentation"],
            "Coverage":mgsj["water"]
        },('size.only-starting-area',))
    },
    ("gui-map-generator.enemy-tab-title",):{},
    ("gui-map-generator.advanced-tab-title",):{
        "Record replay information":fa_menu.setting_menu_bool(
            ('gui-map-generator.enable-replay',),
            ('gui-map-generator.enable-replay-description',),False,False),
        ('gui-map-generator.map-size-group-tile',):{
            "Width":mgsj["width"],
            "Height":mgsj["height"],
        },  
        ('gui-map-generator.recipes-difficulty-group-tile',):{
            "Difficulty":msj["difficulty_settings"]["recipe_difficulty"],
        },
        ('gui-map-generator.technology-difficulty-group-tile',):{
            "Difficulty":msj["difficulty_settings"]["technology_difficulty"],
            "Price multiplier":msj["difficulty_settings"]["technology_price_multiplier"],
        },
        ('gui-map-generator.pollution',):autoplace_enable_disable_menu(('gui-map-generator.pollution',),{
            "Absorption modifier":msj["pollution"]["ageing"],
            "Attack cost modifier":msj["pollution"]["enemy_attack_pollution_consumption_modifier"],
            "Minimum to damage trees":msj["pollution"]["min_pollution_to_damage_trees"],
            "Absorbed per damaged tree":msj["pollution"]["pollution_restored_per_tree_damage"],
            "Diffusion ratio":msj["pollution"]["diffusion_ratio"],
        })
    }
}

msj["pollution"]["enabled"]=menu[("gui-map-generator.advanced-tab-title",)][('gui-map-generator.pollution',)].submenu[1]



for name,control in data['autoplace-control'].items():
    submenu={}
    name= control['localised_name'] if 'localised_name' in control else ('autoplace-control-names.'+control['name'],)
    if control['category'] == 'resource':
        parent=menu[("gui-map-generator.resources-tab-title",)]
        submenu['frequency']=fa_menu.setting_menu_float(("gui-map-generator.frequency",),("gui-map-generator.resource-frequency-description",),1,1)
        submenu['size']=fa_menu.setting_menu_float(("gui-map-generator.size",),("gui-map-generator.resource-size-description",),1,1)
        if 'richness' in control and control['richness']:
            submenu['richness']=fa_menu.setting_menu_float(("gui-map-generator.richness",),("gui-map-generator.resource-richness-description",),1,1)
        name=('entity-name.'+control['name'],)
    elif control['category'] == 'terrain':
        parent=menu[("gui-map-generator.terrain-tab-title",)]
        submenu['frequency']=menu_setting_inverse_float(("gui-map-generator.scale",),("gui-map-generator.terrain-scale-description",),1,1)
        submenu['size']=fa_menu.setting_menu_float(("gui-map-generator.coverage",),("gui-map-generator.terrain-coverage-description",),1,1)
    else:
        parent=menu[("gui-map-generator.enemy-tab-title",)]
        submenu['frequency']=fa_menu.setting_menu_float(("gui-map-generator.frequency",),("gui-map-generator.enemy-frequency-description",),1,1)
        submenu['size']=fa_menu.setting_menu_float(("gui-map-generator.size",),("gui-map-generator.enemy-size-description",),1,1)

    if 'can_be_disabled' not in control or control['can_be_disabled']:
        my_menu = autoplace_enable_disable_menu(name,submenu)
    else:
        my_menu = fa_menu.menu_item(name,submenu)
    parent[control['name']]=my_menu
    mgsj["autoplace_controls"][control['name']]=submenu

menu[("gui-map-generator.terrain-tab-title",)].update({
    "Cliffs":autoplace_enable_disable_menu(("gui-map-generator.cliffs",),{
        "Frequency":mgsj["cliff_settings"]["cliff_elevation_interval"],
        "Conitnuity":mgsj["cliff_settings"]["richness"]
    }),
    "Moisture":fa_menu.menu_item(("gui-map-generator.moisture",),{
        "Scale":mgsj["property_expression_names"]["control-setting:moisture:frequency:multiplier"],
        "Bias":mgsj["property_expression_names"]["control-setting:moisture:bias"],
    },("gui-map-generator.moisture-description",)),
    "Terain type":fa_menu.menu_item(("gui-map-generator.aux",),{
        "Scale":mgsj["property_expression_names"]["control-setting:aux:frequency:multiplier"],
        "Bias":mgsj["property_expression_names"]["control-setting:aux:bias"],
    },("gui-map-generator.aux-description",))
})

menu[("gui-map-generator.enemy-tab-title",)].update({
    "Peaceful mode":mgsj["peaceful_mode"],
    "Starting area size":mgsj["starting_area"],
    "Enemy Expansion":autoplace_enable_disable_menu(("gui-map-generator.enemy-expansion-group-tile",),{
        "Maximum expanstion distance":msj["enemy_expansion"]["max_expansion_distance"],
        "Minimum group size":msj["enemy_expansion"]["settler_group_min_size"],
        "Maximum group size":msj["enemy_expansion"]["settler_group_max_size"],
        "Minimum cooldown":msj["enemy_expansion"]["min_expansion_cooldown"],
        "Maximum cooldown":msj["enemy_expansion"]["max_expansion_cooldown"],
    }),
    "Evolution":autoplace_enable_disable_menu(("gui-map-generator.evolution",),{
        "Time factor":msj["enemy_evolution"]["time_factor"],
        "Destroy factor":msj["enemy_evolution"]["destroy_factor"],
        "Pollution factor":msj["enemy_evolution"]["pollution_factor"]
    })
})
mgsj["cliff_settings"]["enabled"]=menu[("gui-map-generator.terrain-tab-title",)]["Cliffs"].submenu[1]
msj["enemy_expansion"]["enabled"]=menu[("gui-map-generator.enemy-tab-title",)]["Enemy Expansion"].submenu[1]
msj["enemy_evolution"]["enabled"]=menu[("gui-map-generator.enemy-tab-title",)]["Evolution"].submenu[1]

class SettingEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, fa_menu.menu_item):
            return obj.val
        # Let the base class default method raise the TypeError
        return super().default(obj)



main_menu=fa_menu.menu_item('Main Menu',menu,None,False)
main_menu()