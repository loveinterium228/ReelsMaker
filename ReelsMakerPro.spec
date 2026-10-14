# -*- mode: python ; coding: utf-8 -*-
#

import os

binaries = []
for name in ('ffmpeg.exe', 'ffprobe.exe'):
    candidate = os.path.join('vendor', name)
    if os.path.exists(candidate):
        binaries.append((candidate, 'ffmpeg/bin'))

datas = [
    ('resources/icon.png', 'resources'),
    ('resources/icon.ico', 'resources'),
    ('resources/styles_dark.qss', 'resources'),
    ('resources/styles_light.qss', 'resources'),
]
for folder in ('resources/icons', 'resources/presets'):
    if os.path.isdir(folder):
        datas.append((folder, folder))
for extra in ('vendor/FFMPEG-LICENSE.txt',):
    if os.path.exists(extra):
        datas.append((extra, '.'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=['qtawesome'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'pydoc_data',
        'PyQt5.QtWebEngineCore',
        'PyQt5.QtWebEngineWidgets',
        'PyQt5.QtQml',
        'PyQt5.QtQuick',
        'PyQt5.QtMultimedia',
        'PyQt5.QtBluetooth',
        'PyQt5.QtPositioning',
        'PyQt5.QtSensors',
        'PyQt5.QtSerialPort',
        'PyQt5.QtSql',
        'PyQt5.QtTest',

        'faster_whisper',
        'ctranslate2',
        'onnxruntime',
        'av',
        'torch',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ReelsMakerPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,

    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ReelsMakerPro',
)
