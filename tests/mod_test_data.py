# run with -m tests.mod_test_data
from pathlib import Path
from json import dump
from urllib.parse import quote

from factorio_web import get_json

URL = "https://mods.factorio.com/api/mods"

self_path = Path(__file__)
output = self_path.with_suffix(".json")
folder, name = self_path.relative_to(self_path.parent.parent).with_suffix("").parts
cmd = f"python -m {folder}.{name}"
params = {"hide_deprecated": "false", "page_size": "max"}
results = []
data = {
    "_comment": f"Auto generated from web api by running `{cmd}`",
    "pagination": None,
    "results": results,
}
full_list = get_json(URL, params)["results"]
chunk_size = 20
for mod in full_list:
    partial = get_json(f"{URL}/{quote(mod['name'])}/full")
    results.append(partial)
    print(mod["name"])
with output.open("w", encoding="utf8") as fp:
    dump(data, fp, indent=2, ensure_ascii=False)
