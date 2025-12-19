import subprocess
import re
import os
import zipfile
import time
from shutil import rmtree
from sys import platform

from credentials import get_credentials
from factorio_web import get_json, download
from fa_paths import BIN, TEMP, FACTORIO_VERSION

debug = False

download_package_map = {"win32": "win64-manual", "darwin": "osx", "linux": "linux64"}
download_package = download_package_map[platform]

if not download_package:
    raise ValueError("Unsupported Platform:" + platform)

package_map = {
    ("win64", "full"): "core-win64",
    ("linux64", "full"): "core-linux64",
    ("mac", "full"): "core-mac",
}

FACTORIO_INSTALL_PATH = "./"


def get_latest_stable():
    return get_json("https://factorio.com/api/latest-releases")["stable"]["alpha"]


def delete_dir_if_exists(dirname):
    if os.path.exists(dirname):
        print("deleting " + dirname)
        rmtree(dirname)


def overwrite_factorio_install_from_new_zip(filename):
    delete_dir_if_exists(FACTORIO_INSTALL_PATH + "bin")
    delete_dir_if_exists(FACTORIO_INSTALL_PATH + "data")
    delete_dir_if_exists(FACTORIO_INSTALL_PATH + "doc-html")
    print("extracting new installation")
    with zipfile.ZipFile(filename) as zp:
        my_path = zipfile.Path(zp)
        nested_dir = next(my_path.iterdir())
        print(nested_dir.name)
        # zp.extractall(FACTORIO_INSTALL_PATH)
    print("done extracting. Deleting download.")


# function totally a work in progress don't attempt to use
def install():
    version = input("Enter version to download. Leave blank for latest stable:")
    if not version:
        version = get_latest_stable()
    TEMP().mkdir(exist_ok=True)
    filename = TEMP() / f"factorio-{version}-{download_package}"
    print("Downloading version " + version)
    download(
        f"https://www.factorio.com/get-download/{version}/alpha/{download_package}",
        filename,
    )
    overwrite_factorio_install_from_new_zip(filename)


def get_current_version():
    version_str = subprocess.check_output([str(BIN()), "--version"]).decode("utf-8")
    version_re = r"Version: *([\d\.]+) *\( *([^,]+), *([^,]+), *([^)]+)\)"
    maybe_match = re.match(version_re, version_str)
    if not maybe_match:
        print("could not match version string", version_str)
        return None
    check_type = (maybe_match[3], maybe_match[4])
    if not check_type in package_map:
        print("could not identify package type from:", check_type)
        return None
    return {"from": maybe_match[1], "package": package_map[check_type]}


def check_for_updates(current_version):
    print("checking for Factorio updates...")
    available = get_json("https://updater.factorio.com/get-available-versions")
    if not available:
        print("couldn't get any updates")
        return None
    if current_version["package"] not in available:
        print("no available versions match package. Versions are:")
        for ver in available.keys():
            print("\t", ver)
        return None
    versions = available[current_version["package"]]
    upgrade_list = []
    version = current_version["from"]
    for upgrade in versions:
        if "stable" in upgrade:
            stable = upgrade["stable"]
            break
    else:
        print("no stable version found in available versions")
        return None
    found = True
    while found and version != stable:
        found = False
        for upgrade in versions:
            if "from" in upgrade and upgrade["from"] == version:
                upgrade_list.append(upgrade)
                version = upgrade["to"]
                found = True
                break
    return upgrade_list


def update_filename(current_version, update):
    p = current_version["package"]
    return TEMP() / f"{p}-{update['from']}-{update['to']}-update.zip"


def prep_update(current_version, update_candidates):
    TEMP().mkdir(exist_ok=True)
    params = {}
    params.update(**get_credentials())
    params["package"] = current_version["package"]
    params["apiVersion"] = 2
    for i, update in enumerate(update_candidates):
        this_params = params | update
        print("Downloading " + update["to"])
        download(
            "https://updater.factorio.com/updater/get-download",
            update_filename(params, update),
            this_params,
        )
    print("Finished Downloads")
    return


def process_exists():
    # cSpell:disable-next-line
    call = "TASKLIST", "/FI", "imagename eq Factorio.exe"
    if subprocess.check_output(call).splitlines()[3:]:
        return True


def execute_update(current_version, update_candidates):
    applying = re.compile(r"Applying update .*-(\d+\.\d+\.\d+)-update")
    print(current_version, update_candidates)
    params = [str(BIN())]
    for update in update_candidates:
        file = os.path.abspath(update_filename(current_version, update))
        params.append("--apply-update")
        params.append(file)
    print(params)
    child = subprocess.Popen(params, stdout=subprocess.PIPE)
    if current_version["package"] == "core-win64":
        # the windows UAC makes it so we can't monitor the output
        while process_exists():
            time.sleep(1)
    else:
        assert child.stdout is not None, "stdout should not be None"
        for line in child.stdout:
            print(line)
            if m := applying.search(line.decode()):
                print(f"Applying Update:{m[1]}")
            elif debug:
                print("--", line.decode(), end="")


def cleanup_update(current_version, update_candidates):
    for update in update_candidates:
        file = os.path.abspath(update_filename(current_version, update))
        os.remove(file)


def do_update(confirm=True):
    current_version = get_current_version()
    if not current_version:
        return False
    print(f"Version: {current_version['from']}")
    update_candidates = check_for_updates(current_version)
    if not update_candidates:
        print("no updates available")
        return False
    if confirm:
        input("update to " + update_candidates[-1]["to"] + "? Enter to continue.")
    else:
        print("updating to " + update_candidates[-1]["to"])
    prep_update(current_version, update_candidates)
    execute_update(current_version, update_candidates)
    cleanup_update(current_version, update_candidates)
    print("all-done")


if "__main__" == __name__:
    print(get_current_version())
