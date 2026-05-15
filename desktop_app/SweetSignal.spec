# -*- mode: python ; coding: utf-8 -*-
#
# Frozen build must ship PortAudio DLLs used by python-sounddevice.
# Collect sounddevice (+ bundled data) and prepend _MEIPASS to PATH via pyi_runtime_path.py.
#
# One-folder (onedir) layout — not one-file. One-file unpacks the whole bundle to %TEMP%
# on every cold start, which is slow and often triggers heavy AV / SmartScreen scans on
# first launch. Users run dist/SweetSignal/SweetSignal.exe inside the folder (zip the
# whole SweetSignal directory for distribution).

block_cipher = None

from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

datas = [("src", "src")]
binaries = []
hiddenimports = []

try:
    d, b, h = collect_all("sounddevice")
    datas.extend(d)
    binaries.extend(b)
    hiddenimports.extend(h)
except Exception:
    pass

try:
    datas.extend(collect_data_files("_sounddevice_data"))
except Exception:
    pass
try:
    binaries.extend(collect_dynamic_libs("_sounddevice_data"))
except Exception:
    pass

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=["pyi_runtime_path.py"],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SweetSignal",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="SweetSignal",
)
