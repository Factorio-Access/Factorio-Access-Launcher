import re
import os
import zipfile
from collections import defaultdict

import fa_paths
import translations
import config
from fa_menu import select_option

MOD_NAME='FactorioAccess'
CHANGESET_PATH='config_changes'

config_re = re.compile(r'^([\w-]+)=(.*)')
comment_re = re.compile(r'^;')


#exit(0)

def get_changes_from_fp(fp):
    changes=defaultdict(dict)
    current_comment=''
    current_category=changes['']
    for line in fp:
        if line[0]==';':
            current_comment+=line[1:]
            continue
        if line[0]=='[':
            current_category=changes[line.strip('[] \t\r\n')]
        if match := re.match(config_re,line):
            current_category[match[1]]=(match[2],current_comment)
        current_comment=''
    return changes



def get_all_changes(after='AA'):
    all_changes={}
    for cfg_path in translations.iterate_over_mod_files(CHANGESET_PATH+'/.*\.ini',re.compile('FactorioAccess.*')):
        version=cfg_path.name[:2]
        if version <= after:
            continue
        with cfg_path.open(encoding='utf8') as fp:
            all_changes[version]=get_changes_from_fp(fp)
    return all_changes

def do_config_check():
    with config.current_conf:
        current=''
        try:
            for i in ['1','2']:
                current+=config.current_conf.get_setting('controls',f'access-config-version{i}-DO-NOT-EDIT')
        except config.Config_Missing:
            current='AA'
        change_sets=get_all_changes(after=current)
        if not change_sets:
            return
        p='''There are changes that the Factorio Access mod recommends making to your cofiguration file that have not yet been applied.
These can be applied interactively or all at once.
How would you like to proceed?'''
        ops=[
            "Interactively approve changes.",
            "Approve all",
            "Skip for now (not recommended)"
        ]
        approve_type=select_option(ops,p)
        if approve_type==2:
            return
        ops=[
            "Approve change",
            "Keep Current",
            "Edit Value",
            "Approve All"
        ]
        for change_set_v, change_set in change_sets.items():
            for cat,changes in change_set.items():
                for setting,change in changes.items():
                    try:
                        current_val=config.current_conf.get_setting(cat,setting)
                    except config.Config_Missing as e:
                        print(e)
                        continue
                    if current_val==change[0]:
                        continue
                    if approve_type==0:
                        cats_to_try=translations.check_cats[cat]
                        p=translations.translate(["",
                            f"{cat}.{setting}\n",
                            ["?"]+[[f"{t_cat}.{setting.removesuffix('-alternative')}"] for t_cat in cats_to_try]+[""],"\n",
                            ["?"]+[[f"{t_cat}-description.{setting}"] for t_cat in cats_to_try]+[""],"\n",
                            change[1],
                            "Current Value:"+current_val+"\n"+
                            "Suggested Value:"+change[0]
                            ])
                        action=select_option(ops,p)
                        if action==1:
                            continue
                        elif action==2:
                            change=(input("New Value:"),)
                        elif action==3:
                            approve_type=1
                    config.current_conf.set_setting(cat,setting,change[0],force=True)
            for i,key in enumerate(change_set_v):
                config.current_conf.set_setting('controls',f'access-config-version{i+1}-DO-NOT-EDIT',key,force=True)


if __name__ == "__main__":
    do_config_check()