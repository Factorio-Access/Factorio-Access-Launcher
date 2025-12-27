__all__ = ["version"]

from pathlib import Path
from subprocess import check_output
import re

from version_type import Launcher_Version

git_folder = Path(__file__).parent


def do_git_cmd(cmd: str):
    cmd_args = cmd.split(" ")
    assert cmd_args[0] == "git"
    cmd_args.insert(1, "-C")
    cmd_args.insert(2, str(git_folder))
    return check_output(cmd_args, text=True).strip()


ver_info = do_git_cmd("git describe --tags --long --dirty").split("-")
if ver_info[-1] == "dirty":
    dirty = True
    ver_info.pop()
else:
    dirty = False
commit = ver_info.pop()
commits_since_ref = ver_info.pop()
tag = "-".join(ver_info)

# check for multiple tags matching the tagged commit
tag_format = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)")
vers: set[tuple[int, int, int]] = set()
for t in do_git_cmd(f"git tag --points-at {tag}").split("\n"):
    if m := tag_format.fullmatch(t):
        vers.add((int(m[1]), int(m[2]), int(m[3])))
if vers:
    tag = ".".join(map(str, max(vers)))

if commits_since_ref != "0":  # since no tag, try to get a branch name
    commit = do_git_cmd("git describe --all --long").removeprefix("heads/")
if dirty:
    commit += "-dirty"
tag += "." + str(commits_since_ref)
version = Launcher_Version(tag, commit)
if __name__ == "__main__":
    print(f"{version=}")
