"""
Launcher self-update module.

Checks GitHub releases for newer versions and handles download/replacement.
Windows only - source users and other platforms are skipped silently.
"""

import sys
import os
import urllib.request
import urllib.error
import json
from pathlib import Path

from packaging.version import Version

from version import version

REPO_OWNER = "Factorio-Access"
REPO_NAME = "Factorio-Access-Launcher"
RELEASES_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
ASSET_NAME = "launcher.exe"

opener = urllib.request.build_opener()
opener.addheaders = [
    ("User-agent", "Factorio-Access/Factorio-Access-Launcher"),
]


class UpdateCheckFailed(Exception):
    """Raised when update check fails in an unexpected way."""
    pass


# Timeout for network requests (seconds)
REQUEST_TIMEOUT = 5


def get_latest_release() -> dict | None:
    """
    Fetch latest release info from GitHub API.

    Returns None silently for expected failures (no network, server errors, rate limits).
    Raises UpdateCheckFailed for unexpected failures (bad response format).
    """
    try:
        with opener.open(RELEASES_URL, timeout=REQUEST_TIMEOUT) as fp:
            data = json.load(fp)

            # Validate expected fields exist
            if not isinstance(data, dict):
                raise UpdateCheckFailed(f"Expected dict from GitHub API, got {type(data).__name__}")
            if "tag_name" not in data:
                raise UpdateCheckFailed("GitHub release missing 'tag_name' field")
            if "assets" not in data:
                raise UpdateCheckFailed("GitHub release missing 'assets' field")

            return data

    except urllib.error.HTTPError as e:
        # Server errors, auth issues, rate limits - fail silently
        if e.code >= 400:
            print(f"GitHub returned {e.code}, skipping update check.")
            return None
        raise

    except urllib.error.URLError as e:
        # Network unreachable, timeout, DNS failure - fail silently
        print("Could not reach GitHub, skipping update check.")
        return None

    except json.JSONDecodeError as e:
        # Got a response but it's not valid JSON - this is unexpected
        raise UpdateCheckFailed(f"Invalid JSON from GitHub API: {e}")


def is_newer(latest_tag: str, current_tag: str) -> bool:
    """
    Compare version tags to determine if latest is newer.

    Current tag format from version.py: "2.0.9.0" (includes commits since tag)
    GitHub tag format: "2.0.9"
    """
    latest = Version(latest_tag)
    current = Version(current_tag)
    return latest > current


def get_asset_url(release: dict) -> str | None:
    """Extract download URL for launcher.exe from release assets."""
    for asset in release.get("assets", []):
        if asset.get("name") == ASSET_NAME:
            return asset.get("browser_download_url")
    return None


def download_update(url: str, dest: Path) -> bool:
    """Download the update file with progress reporting."""
    try:
        print("Downloading update...")
        with opener.open(url) as dl, open(dest, "wb") as fp:
            length = dl.getheader("content-length")
            if length:
                length = int(length)
                print(f"Download size: {length // 1024} KB")

            buff_size = 8192
            bytes_done = 0
            last_percent = -1

            while True:
                buffer = dl.read(buff_size)
                if not buffer:
                    break
                fp.write(buffer)
                bytes_done += len(buffer)

                if length:
                    percent = bytes_done * 100 // length
                    # Report every 10%
                    if percent >= last_percent + 10:
                        print(f"{percent}%")
                        last_percent = percent

        print("Download complete.")
        return True
    except urllib.error.URLError as e:
        print(f"Download failed: {e}")
        return False


def get_current_exe() -> Path | None:
    """Get path to currently running executable, or None if running from source."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable)
    return None


def cleanup_old_exe():
    """Remove old/new exe files from previous update, if present."""
    current_exe = get_current_exe()
    if not current_exe:
        return
    for suffix in (".exe.old", ".exe.new"):
        stale_file = current_exe.with_suffix(suffix)
        if stale_file.exists():
            try:
                stale_file.unlink()
            except OSError:
                pass  # Ignore if can't delete


def apply_update(new_exe: Path) -> bool:
    """
    Replace current exe with new one and restart.

    On Windows, we can rename a running exe but not delete it.
    So we:
    1. Rename current exe to .old
    2. Move new exe into place
    3. Launch new exe (inherits console)
    4. Exit current process
    5. Next startup cleans up .old file
    """
    import subprocess

    if sys.platform != "win32":
        print("Auto-update only supported on Windows.")
        print(f"Please manually replace with: {new_exe}")
        return False

    current_exe = get_current_exe()
    if not current_exe:
        print("Cannot apply update when running from source.")
        return False
    old_exe = current_exe.with_suffix(".exe.old")

    print("Applying update...")

    try:
        # Remove previous old exe if it exists
        if old_exe.exists():
            old_exe.unlink()

        # Rename running exe to .old (Windows allows this)
        current_exe.rename(old_exe)

        # Move new exe into place
        new_exe.rename(current_exe)

    except OSError as e:
        print(f"Failed to apply update: {e}")
        return False

    print("Update applied. Restarting...")

    # Launch new exe - inherits console from parent
    subprocess.Popen([str(current_exe)])
    return True


def check_and_update() -> bool:
    """
    Main update check function.

    Returns True if an update is being applied (caller should exit).
    Returns False if no update needed or update failed.
    Only runs when executing as a frozen exe - source users are skipped silently.
    """
    # Skip entirely if running from source
    if not get_current_exe():
        return False

    # Clean up from previous update
    cleanup_old_exe()

    print("Checking for updates...")

    release = get_latest_release()
    if not release:
        return False

    # tag_name validated by get_latest_release()
    latest_tag = release["tag_name"]
    current_tag = version.tag

    print(f"Current version: {current_tag}")
    print(f"Latest version: {latest_tag}")

    if not is_newer(latest_tag, current_tag):
        print("Already up to date.")
        return False

    print(f"Update available: {latest_tag}")

    asset_url = get_asset_url(release)
    if not asset_url:
        print(f"Could not find {ASSET_NAME} in release assets.")
        return False

    # Download next to current exe (must be same drive for rename to work)
    current_exe = get_current_exe()
    new_exe = current_exe.with_suffix(".exe.new")

    if not download_update(asset_url, new_exe):
        return False

    # Apply update (will exit process if successful)
    if apply_update(new_exe):
        sys.exit(0)

    return False


if __name__ == "__main__":
    # For testing
    print(f"Current version: {version.tag}")
    release = get_latest_release()
    if release:
        print(f"Latest release: {release.get('tag_name')}")
        print(f"Is newer: {is_newer(release.get('tag_name', ''), version.tag)}")
