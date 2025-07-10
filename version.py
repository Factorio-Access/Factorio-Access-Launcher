__all__ = ["version"]

from pathlib import Path
from subprocess import check_output

from version_type import Launcher_Version


parent = Path(__file__).parent

cmd: list[str] = []
cmd += "git describe --tags --long --dirty".split(" ")
cmd.insert(1, "-C")
cmd.insert(2, str(parent))
ver_info = check_output(cmd, text=True).strip().split("-")
if ver_info[-1] == "dirty":
    dirty = True
    ver_info.pop()
else:
    dirty = False
commit = ver_info.pop()
commits_since_ref = ver_info.pop()
tag = "-".join(ver_info) + "." + str(commits_since_ref)

if commits_since_ref != "0":
    cmd = cmd[:4] + "--all --long".split(" ")
    branch_info = check_output(cmd, text=True).strip()
    if branch_info.startswith("heads/"):
        commit = branch_info.removeprefix("heads/")
if dirty:
    commit += "-dirty"
version = Launcher_Version(tag, commit)
if __name__ == "__main__":
    print(f"{version=}")
