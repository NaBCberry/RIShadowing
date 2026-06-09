#!/usr/bin/env python3
"""
RIShadowing — 一键构建脚本

用法:
    python build.py                   # 仅打包 Lite 安装版
    python build.py --portable        # 仅打包 Lite 便携版
    python build.py --full            # Lite 安装版 + Full 便携版（含模型）
    python build.py --all             # 全部 4 个产物
    python build.py --skip-installer  # 跳过 Inno Setup
    python build.py --version 1.3.1   # 指定版本号（默认读取 version.txt）
"""

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DIST_WORK = PROJECT_ROOT / "dist_work"
DIST_OUTPUT = PROJECT_ROOT / "dist_output"


def read_version() -> str:
    return PROJECT_ROOT.joinpath("version.txt").read_text(encoding="utf-8").strip()


def clean():
    for p in [DIST_WORK, DIST_OUTPUT]:
        if p.exists():
            try:
                shutil.rmtree(p, ignore_errors=True)
            except Exception:
                pass
    if not DIST_WORK.exists():
        DIST_WORK.mkdir(parents=True)
    if not DIST_OUTPUT.exists():
        DIST_OUTPUT.mkdir(parents=True)


def pyinstaller_build():
    print("=" * 60)
    print("  [1/3] PyInstaller — packaging application")
    print("=" * 60)

    spec = PROJECT_ROOT / "build.spec"
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(spec), "--distpath", str(DIST_WORK)],
        cwd=PROJECT_ROOT,
    )
    if result.returncode != 0:
        print("[ERROR] PyInstaller failed")
        sys.exit(1)

    exe_dir = DIST_WORK / "RIShadowing"
    if not exe_dir.exists():
        print(f"[ERROR] PyInstaller output not found at {exe_dir}")
        sys.exit(1)

    print(f"[OK] PyInstaller output at {exe_dir}")
    return exe_dir


def copy_extra_files(exe_dir: Path):
    for name in ["config.example.json", ".env.example", "AGENTS.md", "version.txt"]:
        src = PROJECT_ROOT / name
        if src.exists():
            shutil.copy2(src, exe_dir / name)
    print("[OK] Extra files copied")


def make_installer(version: str, include_model: bool):
    print("=" * 60)
    label = "Full" if include_model else "Lite"
    print(f"  [2/3] Inno Setup — creating {label} installer")
    print("=" * 60)

    exe_dir = DIST_WORK / "RIShadowing"
    if not exe_dir.exists():
        print("[ERROR] Run PyInstaller first")
        return

    iss_path = PROJECT_ROOT / "installer.iss"
    iss_content = PROJECT_ROOT.joinpath("installer.iss.template").read_text(
        encoding="utf-8"
    )
    iss_content = iss_content.replace("{VERSION}", version)

    if include_model:
        iss_content = iss_content.replace(
            "; Source: \"dist_work\\RIShadowing\\vosk-model*", "Source: \"dist_work\\RIShadowing\\vosk-model*"
        )

    iss_path.write_text(iss_content, encoding="utf-8")

    iscc = _find_iscc()
    if not iscc:
        print("[WARN] Inno Setup (iscc.exe) not found, skipping installer")
        return

    result = subprocess.run(
        [str(iscc), str(iss_path)],
        cwd=PROJECT_ROOT,
    )
    if result.returncode != 0:
        print("[ERROR] Inno Setup failed")
        sys.exit(1)

    suffix = "Full" if include_model else "Lite" if not include_model else "Setup"
    installer_name = f"RIShadowing_{version}_{suffix}_Setup.exe"

    for f in DIST_OUTPUT.iterdir():
        if f.suffix == ".exe":
            target = DIST_OUTPUT / installer_name
            if f != target:
                f.rename(target)
            print(f"[OK] Installer: {target}")
            break


def make_portable(version: str, include_model: bool):
    print("=" * 60)
    label = "Full" if include_model else "Lite"
    print(f"  [3/3] Creating {label} portable zip")
    print("=" * 60)

    exe_dir = DIST_WORK / "RIShadowing"
    if not exe_dir.exists():
        print("[ERROR] Run PyInstaller first")
        return

    zip_name = f"RIShadowing_{version}_Portable_{label}.zip"
    zip_path = DIST_OUTPUT / zip_name

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(exe_dir):
            for file in files:
                fpath = Path(root) / file
                arcname = str(fpath.relative_to(exe_dir))
                if arcname.startswith("vosk-model") and not include_model:
                    continue
                zf.write(fpath, arcname)

    print(f"[OK] Portable: {zip_path}")


def _find_iscc() -> Path | None:
    candidates = [
        Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"))
        / "Inno Setup 6"
        / "ISCC.exe",
        Path(os.environ.get("PROGRAMW6432", "C:\\Program Files"))
        / "Inno Setup 6"
        / "ISCC.exe",
        Path("C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"),
        Path("C:\\Program Files\\Inno Setup 6\\ISCC.exe"),
    ]
    for c in candidates:
        if c.exists():
            return c

    result = subprocess.run(
        ["where", "iscc"], capture_output=True, text=True, shell=True
    )
    if result.returncode == 0 and result.stdout.strip():
        path = result.stdout.strip().split("\n")[0].strip()
        if os.path.isfile(path):
            return Path(path)
    return None


def main():
    parser = argparse.ArgumentParser(
        description="RIShadowing Build Script",
    )
    parser.add_argument("--version", default=None, help="Version number")
    parser.add_argument("--full", action="store_true", help="Include Vosk model in portable")
    parser.add_argument("--portable", action="store_true", help="Only portable zip")
    parser.add_argument("--installer", action="store_true", help="Only installer")
    parser.add_argument("--all", action="store_true", help="All variants")
    parser.add_argument("--skip-installer", action="store_true", help="Skip Inno Setup")
    args = parser.parse_args()

    version = args.version or read_version()
    print(f"Building version: {version}")

    clean()
    exe_dir = pyinstaller_build()
    copy_extra_files(exe_dir)

    do_portable = args.portable or args.all or not args.installer
    do_installer = (args.installer or args.all or not args.portable) and not args.skip_installer

    if do_installer:
        make_installer(version, include_model=False)

    if do_portable:
        make_portable(version, include_model=False)
        if args.full or args.all:
            vosk_dirs = list(PROJECT_ROOT.glob("vosk-model*"))
            if not vosk_dirs:
                print(
                    "[WARN] No Vosk model found in project root, "
                    "Full portable will not include model"
                )
            else:
                for vd in vosk_dirs:
                    shutil.copytree(vd, exe_dir / vd.name, dirs_exist_ok=True)
            make_portable(version, include_model=True)

    print("\n" + "=" * 60)
    print(f"  BUILD COMPLETE — output in {DIST_OUTPUT}")
    print("=" * 60)
    for f in sorted(DIST_OUTPUT.iterdir()):
        size_mb = f.stat().st_size / 1024 / 1024
        print(f"    {f.name} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
