from collections.abc import Iterable
import json
import re
import zipfile
import pathlib
from urllib import parse
from collections import defaultdict
from typing import Iterator, Union

import config
from fa_paths import MODS, READ_DIR
from fa_arg_parse import dprint
from update_factorio import download, get_credentials, opener

_mod_portal = "https://mods.factorio.com"


class mod_version(tuple):
   def __new__(cls, version: str):
      return super().__new__(cls,(int(n) for n in version.split('.')))
   def __repr__(self) -> str:
      return ".".join(str(n) for n in self)

class dependancy(object):
   __comp_map = {
      '<':mod_version.__lt__,
      '<=':mod_version.__le__,
      '=':mod_version.__eq__,
      '>=':mod_version.__ge__,
      '>':mod_version.__gt__,
      }
   __re=re.compile(r'(!|\?|\(\?\)|~|)\s*(\S+)(?:\s*([><=]+)\s*(\d+\.\d+\.\d+))?')
   def __init__(self,dep:str) -> None:
      m=self.__re.fullmatch(dep)
      if not m:
         raise ValueError(f"Unmatched mod dependancy {dep}")
      self.name = m[2]
      self.type = m[1]
      if m[4]:
         self.comp = self.__comp_map[m[3]]
         self.ver = mod_version(m[4])
      else:
         self.comp = None
   def meets(self,other:mod_version):
      if not self.comp:
         return True
      return self.comp(other,self.ver)

class mod_version(tuple):
   def __new__(cls, version: str):
      return super().__new__(cls,(int(n) for n in version.split('.')))
   def __repr__(self) -> str:
      return ".".join(str(n) for n in self)

class dependancy(object):
   __comp_map = {
      '<':mod_version.__lt__,
      '<=':mod_version.__le__,
      '=':mod_version.__eq__,
      '>=':mod_version.__ge__,
      '>':mod_version.__gt__,
      }
   __re=re.compile(r'(!|\?|\(\?\)|~|)\s*(\S+)(?:\s*([><=]+)\s*(\d+\.\d+\.\d+))?')
   def __init__(self,dep:str) -> None:
      m=self.__re.fullmatch(dep)
      if not m:
         raise ValueError(f"Unmatched mod dependancy {dep}")
      self.name = m[2]
      self.type = m[1]
      if m[4]:
         self.comp = self.__comp_map[m[3]]
         self.ver = mod_version(m[4])
      else:
         self.comp = None
   def meets(self,other:mod_version):
      if not self.comp:
         return True
      return self.comp(other,self.ver)

class mod(object):
   def __init__(self,path:Union[zipfile.Path , pathlib.Path]) -> None:
      if path.is_file():
         if not zipfile.is_zipfile(path):
            raise ValueError(f"non zip file {path} failed mod init")
         self.folder_path = next(zipfile.Path(path).iterdir())
      else:
         self.folder_path = path
      info_path = self.folder_path.joinpath("info.json")
      if not info_path.is_file():
         raise ValueError(f"no info file in {self.folder_path}; failed mod init")
      with info_path.open(encoding='utf8') as fp:
         self.info = json.load(fp)
      i=self.info
      self.name = i["name"]
      self.version = mod_version(i["version"])
      re_name=f"{i['name']}(_{i['version']})?(.zip)?"
      if not re.fullmatch(re_name,path.name):
         raise ValueError(f"""Mod path mismatch:
   mod path: {path}
   name:{path.name}
   re:{re_name}""")
   @staticmethod   
   def _iter_files_sub(parts:list[Union[str,re.Pattern]],path: Union[zipfile.Path , pathlib.Path]):
      if not path.exists():
         return
      if not parts:
         if path.is_file():
               yield path
         return
      part=parts[0]
      if isinstance(part,str):
         yield from mod._iter_files_sub(parts[1:],path.joinpath(part))
         return
      for path_part in path.iterdir():
         if part.fullmatch(path_part.name):
               yield from mod._iter_files_sub(parts[1:],path_part)
   
   def iterate_mods_files(self,parts:list[Union[str,re.Pattern]]):
      yield from self._iter_files_sub(parts,self.folder_path)

   def get_dependencies(self):
      deps= self.info['dependencies'] if 'dependencies' in self.info else []
      return [dependancy(d) for d in deps]


class __mod_manager(object):
   MOD_LIST_FILE = MODS.joinpath('mod-list.json')
   def __init__(self) -> None:
      self.dict = None
      with config.current_conf:
         self.new_enabled = config.other.enable_new_mods == "true"
   def __enter__(self) -> None:
      assert self.dict==None , "Already in a with statement"
      with open(self.MOD_LIST_FILE,'r',encoding='utf8') as fp:
         data = json.load(fp)
      self.dict = { m['name']:m for m in data['mods']}
      
      self.modified = False
      self.by_name_version:defaultdict[str,dict[mod_version,mod]]=defaultdict(dict)
      self.allmods:list[mod] = []
      for mod_path in self._iterate_over_all_mod_paths():
         self.add_mod(mod_path)

         pre_size = len(self.dict) 
         self.dict = {
               name: m for name, m in self.dict.items() if name in self.by_name_version
         }
         if len(self.dict) != pre_size:
               self.modified = True

   def __exit__(self, *args) -> None:
        if self.modified:
            data = {"mods": [m for m in self.dict.values()]}
            with open(self.MOD_LIST_FILE, "w", encoding="utf8") as fp:
                json.dump(data, fp, ensure_ascii=False, indent=2)
        self.dict = None

   def enabled(self) -> list[str]:
        return [name for name, m in self.dict.items() if m["enabled"]]

   def set_enabled(self, name: str, val: bool) -> None:
        assert self.dict
        self.dict[name]["enabled"] = val
        self.modified = True

   def enable(self, name) -> None:
        self.set_enabled(name, True)

   def disable(self, name) -> None:
        self.set_enabled(name, False)

   def select_version(self, name, version):
        self.dict[name]["version"] = version
        self.modified = True

   def check_dep(self, dep:dependancy,do_optional=False):
      if dep.type=='!':
         if dep.name in self.dict:
            return not self.dict[dep.name]['enabled']
         return True
      if dep.name in self.dict:
         current=self.dict[dep.name]
         if 'version' in current:
            current_ver=mod_version(current['version'])
         else:
            current_ver=max(self.by_name_version[dep.name])
         return dep.meets(current_ver)
      if dep.type == '(?)' or (dep.type == '?'  and not do_optional):
         return True
      return False
   
   def force_dep(self, dep:dependancy,do_optional=False):
      if dep.type=='!':
         if dep.name in self.dict:
            self.dict[dep.name]['enabled']=False
         return True
      if dep.name in self.dict:
         current=self.dict[dep.name]
         if 'version' in current:
            current_ver=mod_version(current['version'])
         else:
            current_ver=max(self.by_name_version[dep.name])
         if dep.meets(current_ver):
            return True
         ops = [ver for ver in self.by_name_version[dep.name] if dep.meets(ver)]
         if ops:
            current['enabled']=True
            current['version']=str(ops[-1])
            return True
         if dep.type == '(?)' or (dep.type == '?'  and not do_optional):
            self.dict[dep.name]['enabled']=False
            return True
      if dep.type == '(?)' or (dep.type == '?'  and not do_optional):
         return True
      return self.install_mod(dep)

   def install_mod(self,dep:dependancy):
      with opener.open(f"{_mod_portal}/api/mods/{dep.name}") as fp:
         info=json.load(fp)
      ops = [r for r in info['releases'] if dep.meets(mod_version(r['version']))]
      if not ops:
         raise ValueError(f"No mods on portal matching dependency:{dep}")
      self.download_mod(ops[-1])
      
   def download_mod(self,release):
      cred=get_credentials()
      url=_mod_portal+release['download_url']+'?'+parse.urlencode(cred)
      new_path=MODS.joinpath(release['file_name'])
      download( url, new_path)
      self.add_mod(new_path)
   
   def add_mod(self,mod_path):
      try:
         m=mod(mod_path)
      except Exception as e:
         dprint(e)
         return
      self.allmods.append(m)
      self.by_name_version[m.name][m.version]=m #TODO: check duplicates?
      if self.dict and m.name not in self.dict:
         self.dict[m.name]={
            "name":m.name,
            "enabled":self.new_enabled
         }
         self.modified = True

   fancy = re.compile(r"[*.?()\[\]]")

   def get_mod_path_parts(self, path: Union[zipfile.Path, pathlib.Path]):
        if isinstance(path, pathlib.Path):
            try:
                return path.relative_to(MODS).parts
            except:
                pass
            return path.relative_to(READ_DIR).parts
        parts = []
        while isinstance(path.parent, zipfile.Path):
            parts.append(path.name)
            path = path.parent
        return tuple(parts[::-1])

   def _iterate_over_all_mod_paths(self) -> Iterator[pathlib.Path]:
        for base_core in ["core", "base"]:
            yield READ_DIR.joinpath(base_core)
        yield from MODS.iterdir()

   def iter_mods(
        self, require_enabled=True, mod_filter: re.Pattern = None
    ) -> Iterator[mod]:
        for m in self.dict.values():
            if m["enabled"] or not require_enabled:
                name = m["name"]
                if mod_filter and not mod_filter.fullmatch(name):
                    continue
                ver = "version" in m and m["version"] or max(self.by_name_version[name])
                yield self.by_name_version[name][ver]

   def iter_mod_files(
        self, inner_re_path: str, require_enabled=True, mod_filter: re.Pattern = None
    ) -> Iterator[Union[zipfile.Path, pathlib.Path]]:
        parts = inner_re_path.split("/")
        parts = [
            part if not self.fancy.search(part) else re.compile(part) for part in parts
        ]
        for mod in self.iter_mods(require_enabled, mod_filter):
            yield from mod.iterate_mods_files(parts)


mod_manager = __mod_manager()


if __name__ == "__main__":
   print(dependancy('! stop >= 3.4.5').meets(mod_version('3.4.5')))
   with mod_manager:
      pass
          