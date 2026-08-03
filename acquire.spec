from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = collect_submodules("dissect")
datas = collect_data_files("acquire")
datas += collect_data_files("dissect.target")
datas += collect_data_files("dissect.apfs")

a = Analysis(
    ["src/acquire_launcher/__main__.py"],
    pathex=["src"],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["IPython", "tkinter", "minio"],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="acquire",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch="arm64",
    codesign_identity=None,
    entitlements_file=None,
)
