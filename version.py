import sys

if getattr(sys, "frozen", False):
    from built_version import version
else:
    from pathlib import Path as _path
    from subprocess import check_output as _check_output

    _parent = _path(__file__).parent

    _cmd = "git describe --tags --long --dirty".split(" ")
    _cmd.insert(1, "-C")
    _cmd.insert(2, str(_parent))
    _ver_info = _check_output(_cmd, text=True).strip().split("-")
    if _ver_info[-1] == "dirty":
        dirty = True
        _ver_info.pop()
    else:
        dirty = False
    commit = _ver_info.pop()
    commits_since_ref = _ver_info.pop()
    tag = "-".join(_ver_info)

    branch = ""
    commits_since_branch = 0
    if commits_since_ref != "0":
        _cmd = _cmd[:4] + "--all --long".split(" ")
        _branch_info = _check_output(_cmd, text=True).strip().split("-")
        if _branch_info[0].startswith("heads/"):
            _branch_info.pop()  # commit
            commits_since_branch = int(_branch_info.pop())
            branch = "-".join(_branch_info).removeprefix("heads/")
    with _parent.joinpath("built_version.py").open("w", encoding="utf8") as fp:
        for var, val in globals().items():
            if not var.startswith("_"):
                fp.write(f"{var}={val!r}\n")
