import json
import fa_paths
import os

ore_type=0
menu={
    "Resources":{
        ore_type:{
            "frequency":0,
            "size":0,
            "richness":0
        }
    },
    "Terrain":{
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
    "Enemies":{
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
    "Advanced":{
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
for name,preset_group in data['autoplace-control'].items():
    print(name,preset_group)
