# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Define the paths to your resources
added_files = [
    ('ATTENDANCE.png', '.'),           # Will be copied to root of temp directory
    ('Batangas_State_Logo.png', '.'),  # Same as above
    ('settings.png', '.'),             # Same as above
    ('attendance.db', '.')             # Same as above
]

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=added_files,  # Use our defined file list
    hiddenimports=['PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AttendanceSystem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='icon.ico',
    onefile=True
)