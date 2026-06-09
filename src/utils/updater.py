import os
import sys
import json
import shutil
import zipfile
import subprocess
import threading
from pathlib import Path
from typing import Optional, Callable

import requests

from src.utils.paths import get_app_dir, get_data_dir

GITHUB_REPO = "NaBCberry/RIShadowing"
RELEASE_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def get_current_version() -> str:
    app_dir = get_app_dir()
    vf = os.path.join(app_dir, "version.txt")
    if os.path.isfile(vf):
        return Path(vf).read_text(encoding="utf-8").strip()
    return "0.0.0"


def parse_version(v: str) -> tuple:
    parts = v.strip().lstrip("v").split(".")
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        return (0, 0, 0)


def check_latest_release() -> Optional[dict]:
    try:
        resp = requests.get(RELEASE_API, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        tag = data.get("tag_name", "").lstrip("v")
        return {
            "version": tag,
            "version_tuple": parse_version(tag),
            "html_url": data.get("html_url", ""),
            "body": data.get("body", ""),
            "published_at": data.get("published_at", ""),
            "assets": data.get("assets", []),
        }
    except Exception as e:
        print(f"[Updater] check failed: {e}")
        return None


def find_portable_asset(assets: list) -> Optional[dict]:
    for a in assets:
        name = a.get("name", "")
        if "Portable" in name and "Lite" in name and name.endswith(".zip"):
            return {
                "name": name,
                "url": a.get("browser_download_url", ""),
                "size": a.get("size", 0),
            }
    return None


def find_setup_asset(assets: list) -> Optional[dict]:
    for a in assets:
        name = a.get("name", "")
        if "Setup" in name and name.endswith(".exe"):
            return {
                "name": name,
                "url": a.get("browser_download_url", ""),
                "size": a.get("size", 0),
            }
    return None


def download_asset(url: str, dest: str, progress_callback: Callable = None):
    resp = requests.get(url, stream=True, timeout=30)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))
    downloaded = 0

    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if progress_callback and total > 0:
                pct = int(downloaded * 100 / total)
                progress_callback("downloading", pct, None)

    if progress_callback:
        progress_callback("complete", 100, dest)


def extract_portable_update(zip_path: str, target_dir: str, progress_callback: Callable = None):
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        total = len(names)
        for i, name in enumerate(names):
            zf.extract(name, target_dir)
            if progress_callback:
                pct = int((i + 1) * 100 / total)
                progress_callback("extracting", pct, None)

    if progress_callback:
        progress_callback("complete", 100, target_dir)


def apply_portable_update(zip_path: str, progress_callback: Callable = None):
    target = get_app_dir()
    extract_portable_update(zip_path, target, progress_callback)
    try:
        os.remove(zip_path)
    except Exception:
        pass


def launch_setup(setup_path: str):
    subprocess.Popen([setup_path, "/VERYSILENT", "/SUPPRESSMSGBOXES"],
                     shell=True)
    sys.exit(0)


def run_update_async(
    asset: dict,
    is_portable: bool,
    progress_callback: Callable = None,
    on_complete: Callable = None,
):
    def _run():
        try:
            dest = os.path.join(get_data_dir(), asset["name"])
            if progress_callback:
                progress_callback("downloading", 0, None)

            download_asset(asset["url"], dest, progress_callback)

            if is_portable:
                apply_portable_update(dest, progress_callback)

            if on_complete:
                on_complete(dest if not is_portable else None)

        except Exception as e:
            print(f"[Updater] update failed: {e}")
            if progress_callback:
                progress_callback("error", 0, str(e))

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
