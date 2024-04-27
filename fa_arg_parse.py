import argparse
import sys
import os
import pathlib
import re

parser=argparse.ArgumentParser(prog="Factorio Access Launcher",prefix_chars='-+')

fa=parser.add_argument_group(title="FacotrioAccess",description="Arguments meant just for the launcher. These will not be passed along to Factorio")

fa.add_argument('--fa-debug',action="store_true",help='This will print debugging information intervleaved with the launcher. This includes factorio output which can be quite verbose')
fa.add_argument('--fa-stdout-bytes',action="store_true",help='This will print the facotrio output as bytes')

used=parser.add_argument_group(title="Dual Use",description="Arguments that are passed to factorio and also modify the launcher behavior")

used.add_argument('bin',nargs='?', help="If any possitional arguments exist the whole command is assumed to be used to launch factorio")
used.add_argument('-c','--config',help='config file to use')
used.add_argument(     '--mod-directory',help='Mod directory to use')
used.add_argument(     '--executable-path',metavar='PATH',help='Mod directory to use') 

launch_group=parser.add_argument_group(title="Launch Rrequests",description="Options that will skip the menu and just do the requested thing")
launch_reqs=launch_group.add_mutually_exclusive_group()

launch_reqs.add_argument('--version',dest='launch', help="show version information",action="store_true")
launch_reqs.add_argument('-s','--map2scenario', dest='launch', metavar='FILE',help="map to scenario conversion")
launch_reqs.add_argument('-m','--scenario2map', dest='launch', metavar='[MOD/]NAME',help="map to scenario conversion")
launch_reqs.add_argument('--apply-update',dest='launch', metavar='FILE', help="immediately apply update package")
launch_reqs.add_argument('--create',dest='launch', metavar='FILE',help="create a new map")
launch_reqs.add_argument('--start-server',dest='launch', metavar='FILE',help="start a multiplayer server")
launch_reqs.add_argument('--start-server-load-scenario',dest='launch', metavar='[MOD/]NAME',help="start a multiplayer server and load the specified scenario. The scenario is looked for inside the given mod. If no mod is given, it is looked for in the top-level scenarios directory.")
launch_reqs.add_argument('--start-server-load-latest',dest='launch', action='store_true', help="create a new map")
launch_reqs.add_argument('--benchmark',dest='launch', metavar='FILE', help='load save and run benchmark')
launch_reqs.add_argument('--dump-data', dest='launch', action='store_true',help='dumps data.raw as JSON to the script output folder and exits.')
launch_reqs.add_argument('--dump-icon-sprites', dest='launch', action='store_true',help='dumps all icon sprites as png files to the script output folder and exits.')
launch_reqs.add_argument('--dump-prototype-locale', dest='launch', action='store_true',help='dumps all prototypes name and description (if they have a valid value) to the script output folder and exits.')
launch_reqs.add_argument('--mp-connect', dest='launch', metavar='ADDRESS',help='start factorio and connect to address')
launch_reqs.add_argument('--load-game', dest='launch', metavar='FILE', help='start Factorio and load a game in singleplayer')
launch_reqs.add_argument('--load-scenario', dest='launch', metavar='[MOD/]NAME', help='start Factorio and load the specified scenario in singleplayer. The scenario is looked for inside the given mod. If no mod is given, it is looked for in the top-level scenarios directory.')
launch_reqs.add_argument('--benchmark-graphics', dest='launch', metavar='FILE', help='load save and run it with graphics for benchmark-ticks number of ticks as normal game would')
launch_reqs.add_argument('--join-game-by-steam-id','+connect_lobby', dest='launch', metavar='ID', help='join multiplayer game through steam network')

extra_args_group=parser.add_argument_group(title="argumented parameters",description="Options that have parameters that might otherewise be mistaken as an executable. Not actually used for anything in the launcher")
extra_args_group.add_argument('--map-gen-settings',nargs=1,metavar='FILE')
extra_args_group.add_argument('--map-gen-seed',nargs=1,metavar='SEED')
extra_args_group.add_argument('--map-gen-seed-max',nargs=1,metavar='SEED')
extra_args_group.add_argument('--map-settings',nargs=1,metavar='FILE')
extra_args_group.add_argument('--preset',nargs=1)
extra_args_group.add_argument('--generate-map-preview',nargs=1,metavar='PATH')
extra_args_group.add_argument('--generate-map-preview-random',nargs=1,metavar='COUNT')
extra_args_group.add_argument('--map-preview-size',nargs=1,metavar='SIZE')
extra_args_group.add_argument('--map-preview-scale',nargs=1,metavar='SCALE')
extra_args_group.add_argument('--map-preview-offset',nargs=1,metavar='X,Y')
extra_args_group.add_argument('--noise-outputs',nargs=1,metavar='TAG,TAG,...')
extra_args_group.add_argument('--slope-shading',nargs=1,metavar='SHADEAMOUNT')
extra_args_group.add_argument('--slope-shade-property',nargs=1,metavar='SHADEPROP')
extra_args_group.add_argument('--report-quantities',nargs=1,metavar='PROTOTYPE,...')
extra_args_group.add_argument('--threads',nargs=1,metavar='THREADCOUNT')
extra_args_group.add_argument('--instrument-mod',nargs=1,metavar='MOD')
extra_args_group.add_argument('--until-tick',nargs=1,metavar='TICK')
extra_args_group.add_argument('--benchmark-ticks',nargs=1,metavar='TICKS')
extra_args_group.add_argument('--benchmark-runs',nargs=1,metavar='RUNS')
extra_args_group.add_argument('--output-perf-stats',nargs=1,metavar='FILE')
extra_args_group.add_argument('--password',nargs=1,metavar='PASSWORD')
extra_args_group.add_argument('--fullscreen',nargs=1,metavar='BOOL')
extra_args_group.add_argument('--max-texture-size',nargs=1,metavar='N')
extra_args_group.add_argument('--graphics-quality',nargs=1)
extra_args_group.add_argument('--video-memory-usage',nargs=1)
extra_args_group.add_argument('--force-graphics-preset',nargs=1)
extra_args_group.add_argument('--window-size',nargs=1)
extra_args_group.add_argument('--cache-sprite-atlas',nargs=1,metavar='BOOL')
extra_args_group.add_argument('--port', metavar='N', help='network port to use')
extra_args_group.add_argument('--bind', metavar='ADDRESS[:PORT]', help='IP address (and optionally port) to bind to')
extra_args_group.add_argument('--rcon-port', metavar='N', help='Port to use for RCON')
extra_args_group.add_argument('--rcon-bind', metavar='ADDRESS:PORT', help='IP address and port to use for RCON')
extra_args_group.add_argument('--rcon-password', metavar='PASSWORD', help='Password for RCON')
extra_args_group.add_argument('--server-settings', metavar='FILE', help='Path to file with server settings. See data/server-settings.example.json')
extra_args_group.add_argument('--use-authserver-bans', metavar='BOOL', help='Verify that connecting players are not banned from multiplayer and inform Factorio.com about ban/unban commands.')
extra_args_group.add_argument('--use-server-whitelist', metavar='BOOL', help='If the whitelist should be used.')
extra_args_group.add_argument('--server-whitelist', metavar='FILE', help='Path to file with server whitelist.')
extra_args_group.add_argument('--server-banlist', metavar='FILE', help='Path to file with server banlist.')
extra_args_group.add_argument('--server-adminlist', metavar='FILE', help='Path to file with server adminlist.')
extra_args_group.add_argument('--console-log', metavar='FILE', help='Path to file where a copy of the server\'s log will be stored')
extra_args_group.add_argument('--server-id', metavar='FILE', help='Path where server ID will be stored or read from')

launch_args=sys.argv[1:] # 0th arg was used to launch us

#there may be multiple levels of args
# some of which need -- to be able to pass on args to the next level
# but we don't really care about that and only need to see the flags that factorio cares about
clean_args=[arg for arg in launch_args if arg!='--']
args,_=parser.parse_known_args(clean_args)
def dprint(*pargs,**kargs):
   if args.fa_debug:
      print(*pargs,**kargs)

dprint("We're debugging now :)")
dprint(launch_args)
if args.fa_debug:
   launch_args.remove('--fa-debug')

dprint(args)
