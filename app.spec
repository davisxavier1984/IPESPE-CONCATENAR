# -*- mode: python ; coding: utf-8 -*-

import streamlit as st
import os
import site

# Get Streamlit installation path
streamlit_path = os.path.dirname(st.__file__)

# Get site-packages path
site_packages = site.getsitepackages()[0]

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        (os.path.join(streamlit_path, 'static'), 'streamlit/static'),
        (os.path.join(streamlit_path, 'runtime'), 'streamlit/runtime'),
    ],
    hiddenimports=[
        'streamlit',
        'pandas',
        'openpyxl',
        'xlrd',
        'file_handler',
        'database_processor',
        'validator',
        'streamlit.web.cli',
        'streamlit.runtime.scriptrunner.script_runner',
        'streamlit.components.v1.html',
        'validators',
        'altair',
        'plotly',
        'click',
        'tornado',
        'pyarrow',
        'pydeck',
        'blinker',
        'cachetools',
        'packaging',
        'pillow',
        'protobuf',
        'requests',
        'rich',
        'toml',
        'tzlocal',
        'urllib3',
        'watchdog',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ConsolidadorExcel',
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
    version=None,
    icon=None,
)