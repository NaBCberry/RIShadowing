# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for R.I.Shadowing (Shadowing Practice)

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(SPECPATH)

# --- Block for hidden / custom modules hidden imports ---
hidden_imports = [
    "src",
    "src.app",
    "src.utils.config",
    "src.utils.paths",
    "src.utils.model_downloader",
    "src.utils.error_diagnosis",
    "src.models.db",
    "src.models.material",
    "src.models.practice_record",
    "src.services.audio_player",
    "src.services.audio_recorder",
    "src.services.speech_recognizer",
    "src.services.comparator",
    "src.services.asr",
    "src.services.asr.base",
    "src.services.asr.vosk_asr",
    "src.services.asr.whisper_asr",
    "src.services.tts",
    "src.services.tts.base",
    "src.services.tts.edge_tts",
    "src.services.tts.piper_tts",
    "src.services.tts.pyttsx3_tts",
    "src.gui.styles",
    "src.gui.panels.device_panel",
    "src.gui.panels.input_panel",
    "src.gui.panels.feedback_panel",
    "src.gui.panels.display_panel",
    "src.gui.panels.material_panel",
    "src.gui.panels.download_dialog",
    "src.gui.panels.settings_dialog",
    "customtkinter",
    "sounddevice",
    "soundfile",
    "vosk",
    "edge_tts",
    "openai",
    "pyttsx3",
    "pyttsx3.drivers",
    "pyttsx3.drivers.sapi5",
    "numpy",
    "comtypes",
    "comtypes.client",
    "ctypes",
    "ctypes.wintypes",
    "requests",
    "srt",
    "tqdm",
]

# --- Data files bundled into dist/ root ---
data_files = [
    ("AGENTS.md", "."),
    ("version.txt", "."),
]

block_cipher = None

a = Analysis(
    [str(PROJECT_ROOT / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    module_collection_mode={},
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="R.I.Shadowing",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    contents_directory=".",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    # Include AGENTS.md and version.txt alongside the exe
    first_strip_absolute_paths=False,
    strip=False,
    upx_exclude=[],
    name="R.I.Shadowing",
)
