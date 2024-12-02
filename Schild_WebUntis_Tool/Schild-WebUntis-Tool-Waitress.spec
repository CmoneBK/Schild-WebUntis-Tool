# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['__init__.py'],  # Hauptskript mit korrektem Pfad
    pathex=['.'],  # Füge das aktuelle Verzeichnis zum Suchpfad hinzu
    binaries=[],
    datas=[
        ('templates', 'templates'),  # Templates einfügen
        ('static', 'static')         # Statische Dateien einfügen
    ],
    hiddenimports=[
        'main',      # Manuell hinzuzufügende Module
        'smtp',
        'oauth2client',  # Füge oauth2client explizit hinzu
		'openpyxl',
		'winshell',
		'waitress'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='Schild-WebUntis-Tool-WServer',  # Name der .exe
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
	icon='logo.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
