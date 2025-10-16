import urllib.request
import urllib.error
import json

from fa_paths import MODS
from factorio_web import download

opener = urllib.request.build_opener()
# cSpell:words cloudfare addheaders zipball
# cloudfare rejects the default user agent
opener.addheaders = [
    (
        "User-agent",
        "Factorio-Access/Factorio-Access-Launcher",
    )
]

def get_json(url:str):
    with opener.open(url) as fp:
        return json.load(fp)

BASE = "https://api.github.com/repos/Factorio-Access/FactorioAccess/"

def get_tags(repo:str,user = "Factorio-Access"):
    return get_json(f"https://api.github.com/repos/{user}/{repo}/tags")

def update_if_needed(current_version:str, name:str,user = "Factorio-Access"):
    try:
        tags = get_tags(name,user)
        if not tags:
            print(f"No tags found for {name}")
            return None
        latest = tags[0]["name"]
        if latest == current_version:
            return None
        print(f"Updating {name} to {latest}")
        download(tags[0]["zipball_url"], MODS / f"{name}_{latest.strip(" v")}.zip")
    except urllib.error.URLError:
        print(f"Network Error updating: {name}")
        return None
    return latest

def update_all():
    for _ in range(2):
        try:
            with open(MODS / "git_versions.txt","r+",encoding='utf8') as fp:
                new_file_contents = []
                for line in fp:
                    parts = line.strip().split()
                    if len(parts) != 2:
                        continue
                    name, version = parts
                    new_version = update_if_needed(version,name)
                    if new_version:
                        version = new_version
                    new_file_contents.append(f"{name} {version}\n")
                fp.seek(0)
                fp.truncate(0)
                fp.writelines(new_file_contents)
        except FileNotFoundError:
            with open(MODS / "git_versions.txt","w") as fp:
                fp.write("FactorioAccess none\n")
                fp.write("Kruise_Kontrol_Remote none\n")
        else:
            break

if __name__ == "__main__":
    update_all()