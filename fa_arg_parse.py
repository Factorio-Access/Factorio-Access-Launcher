import argparse
import sys
import os
import pathlib
import re

parser=argparse.ArgumentParser(prog="Factorio Access Launcher",prefix_chars='-+')

fa=parser.add_argument_group(title="FacotrioAccess",description="Arguments meant just for the launcher. These will not be passed along to Factorio")

fa.add_argument('--fa-debug',action="store_true",help='This will print debugging information intervleaved with the launcher. This includes factorio output which can be quite verbose')

used=parser.add_argument_group(title="Dual Use",description="Arguments that are passed to factorio and also modify the launcher behavior")

used.add_argument('bin',nargs='?', help="If any possitional arguments exist the whole command is assumed to be used to launch factorio")
used.add_argument('-c','--config',help='config file to use')
used.add_argument(     '--mod-directory',help='Mod directory to use')

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
