# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

datas = collect_data_files("faster_whisper", includes=["assets/*"])
binaries = (
    collect_dynamic_libs("ctranslate2")
    + collect_dynamic_libs("onnxruntime")
    + collect_dynamic_libs("nvidia.cublas", destdir=".")
    + collect_dynamic_libs("nvidia.cudnn", destdir=".")
)
hiddenimports = [
    "ctranslate2",
    "faster_whisper",
    "onnxruntime",
    "pyaudiowpatch",
    "qtawesome",
    "sacremoses",
    "sentencepiece",
    "transformers.models.marian.configuration_marian",
    "transformers.models.marian.modeling_marian",
    "transformers.models.marian.tokenization_marian",
]

analysis = Analysis(
    ["app/main.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "tkinter"],
    noarchive=False,
)

# The Codex workspace runtime also contains Poppler's ICU 78 DLLs on PATH.
# PyInstaller may pick those up while scanning Qt, but Qt on Windows expects
# the system ICU shim instead. Shipping the Poppler copies makes QtCore fail
# before Python can even enter main().
analysis.binaries = [
    entry
    for entry in analysis.binaries
    if not (
        entry[0].lower() in {"icuuc.dll", "icudt78.dll"}
        and (
            "codex-runtimes" in str(entry[1]).lower()
            or "poppler" in str(entry[1]).lower()
        )
    )
]

pyz = PYZ(analysis.pure)
executable = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="BellenneRelay",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
collection = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=True,
    name="BellenneRelay",
)
