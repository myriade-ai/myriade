# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['../../service/app.py'],
    pathex=[],
    binaries=[],
    datas=[
        (".env", "."),
        ("../../service/alembic.ini", "."),
        ("../../service/migrations", "migrations"),
        ("../../view/dist", "static"),
    ],
    hiddenimports=[
        'engineio.async_drivers.threading',
        'socketio.async_drivers.threading',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'workos',
        'stripe',
        'botocore',  # Maybe needed for Snowflake?
        'pre-commit',
        'virtualenv',
        'grpc',
    ],
    noarchive=False,
    optimize=0,
    windowed=True,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='myriade-exe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    windowed=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Myriade'
)

app = BUNDLE(coll,
    name='Myriade.app',
    icon='icon.icns',
    bundle_identifier='ai.myriade.app',
    version='1.0.0',
    short_version='1.0.0',
    info_plist={
        'CFBundleName': 'Myriade',
        'CFBundleDisplayName': 'Myriade',
        'CFBundleExecutable': 'myriade-exe',
        'LSBackgroundOnly': False,  # Allow console output
        'LSUIElement': False,  # make Dock/icon normal
        'NSPrincipalClass': 'NSApplication',
    },
    console=True,        # keep a terminal window attached
)