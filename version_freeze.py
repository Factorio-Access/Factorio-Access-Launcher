from pathlib import Path
from os import rename, replace, remove

# cSpell:words filevers prodvers

parent = Path(__file__).parent
orig_version = parent.joinpath("version.py").absolute()
temp_version = parent.joinpath("version_temp.py").absolute()
pyinstaller_version_txt = parent.joinpath("version_info.txt")


class frozen(object):
    def __enter__(self):
        from version import version

        rename(orig_version, temp_version)

        with orig_version.open("w", encoding="utf8") as fp:
            fp.write(
                f"""from version_type import Launcher_Version
{version=} 
"""
            )
        ver = tuple([int(i) for i in version.tag.split(".")] + [0])
        with pyinstaller_version_txt.open("w", encoding="utf8") as fp:
            fp.write(
                f"""\
VSVersionInfo(
    ffi=FixedFileInfo(
        filevers={ver},
        prodvers={ver},
        mask=0x3F,
        flags=0x0,
        OS=0x4,
        fileType=0x1,
        subtype=0x0,
        # Creation date and time stamp.
        date=(0, 0),
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    "000004b0",
                    [
                        StringStruct("CompanyName", "Factorio Access"),
                        StringStruct("FileDescription", "Factorio Access Launcher"),
                        StringStruct("FileVersion", "{version.tag}"),
                        StringStruct("InternalName", "Factorio Access Launcher"),
                        StringStruct(
                            "LegalCopyright",
                            "Copyright MIT © 2022-2024 Factorio Access",
                        ),
                        StringStruct("OriginalFilename", "Launcher.exe"),
                        StringStruct("ProductName", "Factorio Access Launcher"),
                        StringStruct("ProductVersion", "{version.tag}"),
                    ],
                )
            ]
        ),
        VarFileInfo([VarStruct("Translation", [0, 1200])]),
    ],
)
"""
            )

    def __exit__(self, *args):
        replace(temp_version, orig_version)
        remove(pyinstaller_version_txt)


if __name__ == "__main__":
    with frozen():
        input("check on version.py")
    input("check on version.py")
