# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = []
hiddenimports += collect_submodules("pydub")

binaries = []
binaries += collect_dynamic_libs("mediapipe")

datas = []
datas += collect_data_files(
    "mediapipe",
    includes=[
        "tasks/**",
        "modules/**",
        "framework/**",
    ],
)

datas += [
    ("assets/sounds/metro_sound.wav", "assets/sounds"),
    ("src/core/shared/beat_detection_model/beat_detector_xy.keras", "src/core/shared/beat_detection_model"),
    ("src/core/live/pose_landmarks/pose_landmarker_lite.task", "src/core/live/pose_landmarks"),
    ("src/core/live/pose_landmarks/pose_landmarker_full.task", "src/core/live/pose_landmarks"),
    ("src/core/live/pose_landmarks/pose_landmarker_heavy.task", "src/core/live/pose_landmarks"),
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PyQt5", "PySide6", "PyQt6", "PySide2"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    exclude_binaries=False,
    name="ConductingTutor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
