import json
from typing import Any, Callable
import weakref

import fa_paths
import os
import fa_menu
from translations import localised_str
from launch_and_monitor import launch_with_params,launch


class enable_disable_menu(fa_menu.menu_item):
    def __init__(self, name: localised_str | Callable[..., Any] | dict, submenu: dict, desc: localised_str | None = None) -> None:
        enabler=enable_disable_submenu(("gui-map-generator.enabled",))
        enabler.parent=weakref.ref(self)
        my_submenu={'enabled':enabler}
        my_submenu.update(submenu)
        self.my_name=name
        super().__init__(self.name, my_submenu, desc, True)
        self.full_submenu=self.submenu
        self.remake_submenu()
    def name(self,*args):
        return ("",self.my_name,": ",self.submenu[1].val_to_string())
    def get_menu_name(self,*args):
        return self.my_name
    def remake_submenu(self):
        if self.submenu[1].val:
            self.submenu=self.full_submenu
        else:
            self.submenu=self.submenu[:2]

class enable_disable_submenu(fa_menu.setting_menu_bool):
    def __call__(self,*args):
        super().__call__(*args)
        parent=self.parent()
        if 'set_others' in self.__dict__:
            if not self.val:
                for sub in parent.submenu[2:]:
                    sub.val=0
            else:
                for sub in parent.submenu[2:]:
                    sub.val=sub.default
        parent.remake_submenu()
        return 0

class autoplace_enable_disable_menu(enable_disable_menu):
    def __init__(self, name: localised_str | Callable[..., Any] | dict, submenu: dict, desc: localised_str | None = None) -> None:
        super().__init__(name, submenu, desc)
        self.submenu[1].set_others = True

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

class menu_seed(fa_menu.setting_menu_int):
    def val_to_string(self):
        if self.val is None:
            return ("gui-map-generator.randomize-map-seed",)
        return f"{self.val}"
    def input_to_val(self, inp: str):
        try:
            self.val = int(inp)
        except:
            self.val = None

data={}

def refresh_data():
    global data
    try:
        with open(fa_paths.SCRIPT_OUTPUT.joinpath('data-raw-dump.json'),encoding='utf8') as fp:
            data=json.load(fp)
    except FileNotFoundError:
        launch_with_params(["--dump-data"],save_rename=False)
        with open(fa_paths.SCRIPT_OUTPUT.joinpath('data-raw-dump.json'),encoding='utf8') as fp:
            data=json.load(fp)
refresh_data()





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

  "seed": menu_seed(('gui-map-generator.map-seed',),('fa-l.map-seed-description',),None,None)
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
                ('gui-map-generator.enemy-attack-pollution-consumption-modifier-description',)),
    "min_to_diffuse": fa_menu.setting_menu_int("min_to_diffuse",None,15,15),
    "expected_max_per_chunk": fa_menu.setting_menu_int("expected_max_per_chunk",None,150,150),
    "min_to_show_per_chunk": fa_menu.setting_menu_int("min_to_show_per_chunk",None,50,50),
    "pollution_with_max_forest_damage": fa_menu.setting_menu_int("pollution_with_max_forest_damage",None,150,150),
    "pollution_per_tree_damage": fa_menu.setting_menu_int("pollution_per_tree_damage",None,50,50),
    "max_pollution_to_restore_trees": fa_menu.setting_menu_int("max_pollution_to_restore_trees",None,20,20),
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
        ('enemy-expansion-maximum-expansion-cooldown-description',), 216000,216000),
    "min_base_spacing": 3,
    "friendly_base_influence_radius": 2,
    "enemy_building_influence_radius": 2,
    "building_coefficient": 0.1,
    "other_base_coefficient": 2.0,
    "neighbouring_chunk_coefficient": 0.5,
    "neighbouring_base_chunk_coefficient": 0.4,
    "max_colliding_tiles_coefficient": 0.9,
  },
  "steering":
  {
    "default":
    {
      "radius": 1.2,
      "separation_force": 0.005,
      "separation_factor": 1.2,
      "force_unit_fuzzy_goto_behavior": False
    },
    "moving":
    {
      "radius": 3,
      "separation_force": 0.01,
      "separation_factor": 3,
      "force_unit_fuzzy_goto_behavior": False
    }
  },
  "unit_group":
  {
    "min_group_gathering_time": 3600,
    "max_group_gathering_time": 36000,
    "max_wait_time_for_late_members": 7200,
    "max_group_radius": 30.0,
    "min_group_radius": 5.0,
    "max_member_speedup_when_behind": 1.4,
    "max_member_slowdown_when_ahead": 0.6,
    "max_group_slowdown_factor": 0.3,
    "max_group_member_fallback_factor": 3,
    "member_disown_distance": 10,
    "tick_tolerance_when_member_arrives": 60,
    "max_gathering_unit_groups": 30,
    "max_unit_group_size": 200
  },
  "path_finder":
  {
    "fwd2bwd_ratio": 5,
    "goal_pressure_ratio": 2,
    "max_steps_worked_per_tick": 100,
    "max_work_done_per_tick": 8000,
    "use_path_cache": True,
    "short_cache_size": 5,
    "long_cache_size": 25,
    "short_cache_min_cacheable_distance": 10,
    "short_cache_min_algo_steps_to_cache": 50,
    "long_cache_min_cacheable_distance": 30,
    "cache_max_connect_to_cache_steps_multiplier": 100,
    "cache_accept_path_start_distance_ratio": 0.2,
    "cache_accept_path_end_distance_ratio": 0.15,
    "negative_cache_accept_path_start_distance_ratio": 0.3,
    "negative_cache_accept_path_end_distance_ratio": 0.3,
    "cache_path_start_distance_rating_multiplier": 10,
    "cache_path_end_distance_rating_multiplier": 20,
    "stale_enemy_with_same_destination_collision_penalty": 30,
    "ignore_moving_enemy_collision_distance": 5,
    "enemy_with_different_destination_collision_penalty": 30,
    "general_entity_collision_penalty": 10,
    "general_entity_subsequent_collision_penalty": 3,
    "extended_collision_penalty": 3,
    "max_clients_to_accept_any_new_request": 10,
    "max_clients_to_accept_short_new_request": 100,
    "direct_distance_to_consider_short_request": 100,
    "short_request_max_steps": 1000,
    "short_request_ratio": 0.5,
    "min_steps_to_check_path_find_termination": 2000,
    "start_to_goal_cost_multiplier_to_terminate_path_find": 500.0,
    "overload_levels": [0, 100, 500],
    "overload_multipliers": [2, 3, 4],
    "negative_path_cache_delay_interval": 20
  },
  "max_failed_behavior_count": 3
}

json_files={
    "basic_settings":mgsj,
    "advanced_settings":msj
    }




selected_preset=None

def get_presets(*args):
    global selected_preset
    presets=[]
    for preset_group in data['map-gen-presets'].values():
        for name,preset in preset_group.items():
            if name=='type' or name=='name':
                continue
            tname=('map-gen-preset-name.'+name,)                
            if args and args[-1]==preset:
                return tname
            preset['name']=name
            presets.append((
                preset['order'] if 'order' in preset else '',
                tname,
                preset
            ))
    presets.sort()
    if selected_preset is None:
        select_preset(presets[0][2])
    for i,p in enumerate(presets):
        if p[2]==selected_preset:
            tname=p[1]
            if check_vals(p[2],json_files) > 0:
                add=('gui-map-generator.custom',)
            else:
                add=('fa-l.selected',)
            tname=('',tname,add)
            presets[i]=(p[0],tname,p[2])
    return {p[1]:p[2] for p in presets}

def select_preset(preset):
    global selected_preset
    selected_preset=preset
    set_vals(preset,json_files)
    return 0

def select_preset_name(preset):
    diffs=check_vals(preset,json_files)
    if diffs >0:
        return ('gui-map-generator.reset-to-preset',diffs)
    return ('gui-map-generator.reset-to-preset-disabled',)

def get_preset_desc(*args):
    preset=args[-1]
    return ("map-gen-preset-description."+preset['name'],)


class SettingEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, fa_menu.menu_item):
            return obj.val
        # Let the base class default method raise the TypeError
        return super().default(obj)

def launch_new(*args):
    mgsp=fa_paths.SCRIPT_OUTPUT.joinpath('map_gen.json')
    msp=fa_paths.SCRIPT_OUTPUT.joinpath('map.json')
    files={
        "basic_settings":mgsp,
        "advanced_settings":msp}
    for sub,path in files.items():
        with open(path,'w',encoding='utf-8') as fp:
            json.dump(json_files[sub],
                    fp,
                    ensure_ascii=False,
                    indent=2,
                    cls=SettingEncoder)
    save=fa_paths.SAVES.joinpath('_autosave-manual.zip').absolute()
    launch_with_params(["--map-gen-settings", str(mgsp), "--map-settings",str(msp),'--create',str(save)],save_rename=False)
    launch(save)
    return 20

menu={
    "seed":mgsj["seed"],
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
        ('gui-map-generator.pollution',):enable_disable_menu(('gui-map-generator.pollution',),{
            "Absorption modifier":msj["pollution"]["ageing"],
            "Attack cost modifier":msj["pollution"]["enemy_attack_pollution_consumption_modifier"],
            "Minimum to damage trees":msj["pollution"]["min_pollution_to_damage_trees"],
            "Absorbed per damaged tree":msj["pollution"]["pollution_restored_per_tree_damage"],
            "Diffusion ratio":msj["pollution"]["diffusion_ratio"],
        })
    },
    ("gui-map-generator.play",):launch_new
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
    "Cliffs":enable_disable_menu(("gui-map-generator.cliffs",),{
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
    "Enemy Expansion":enable_disable_menu(("gui-map-generator.enemy-expansion-group-tile",),{
        "Maximum expanstion distance":msj["enemy_expansion"]["max_expansion_distance"],
        "Minimum group size":msj["enemy_expansion"]["settler_group_min_size"],
        "Maximum group size":msj["enemy_expansion"]["settler_group_max_size"],
        "Minimum cooldown":msj["enemy_expansion"]["min_expansion_cooldown"],
        "Maximum cooldown":msj["enemy_expansion"]["max_expansion_cooldown"],
    }),
    "Evolution":enable_disable_menu(("gui-map-generator.evolution",),{
        "Time factor":msj["enemy_evolution"]["time_factor"],
        "Destroy factor":msj["enemy_evolution"]["destroy_factor"],
        "Pollution factor":msj["enemy_evolution"]["pollution_factor"]
    })
})

mgsj["cliff_settings"]["enabled"]=menu[("gui-map-generator.terrain-tab-title",)]["Cliffs"].submenu[1]
msj["enemy_expansion"]["enabled"]=menu[("gui-map-generator.enemy-tab-title",)]["Enemy Expansion"].submenu[1]
msj["enemy_evolution"]["enabled"]=menu[("gui-map-generator.enemy-tab-title",)]["Evolution"].submenu[1]


sub_preset={
    "_desc_for_presets":get_preset_desc,
    get_presets:{
    select_preset_name:select_preset,
    ('gui-map-generator.next',):menu
}}




def check_vals(preset,obj):
    diffs=0
    for name, subobj in obj.items():
        have_preset=preset and name in preset
        if isinstance(subobj,dict):
            diffs+=check_vals(preset[name] if have_preset else None ,subobj)
            continue
        if not isinstance(subobj,fa_menu.setting_menu):
            continue
        if have_preset:
            check=preset[name]
        else:
            check=subobj.default
        if check != subobj.val:
            diffs+=1
    return diffs

def set_defaults(defs,obj):
    for name, subobj in obj.items():
        if name not in defs:
            continue
        if isinstance(subobj,dict):
            set_defaults(defs[name],subobj)
            continue
        if not isinstance(subobj,fa_menu.setting_menu):
            continue
        subobj.default=defs[name]

def set_vals(preset,obj):
    for name, subobj in obj.items():
        have_preset=preset and name in preset
        if isinstance(subobj,dict):
            set_vals(preset[name] if have_preset else None ,subobj)
            continue
        if not isinstance(subobj,fa_menu.setting_menu):
            continue
        if have_preset:
            subobj.val=preset[name]
        else:
            subobj.val=subobj.default
