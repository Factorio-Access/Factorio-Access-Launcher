import re

import fa_paths
import translations

def get_scenarios():
   scenarios={}
   for path in translations.iterate_over_mod_files('scenarios/.*/description.json',re.compile(r'FactorioAccess.*')):
      parts=translations.get_mod_path_parts(path)
      print(parts)

if __name__ == "__main__":
   get_scenarios()