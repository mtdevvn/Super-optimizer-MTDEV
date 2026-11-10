# Build on Windows x64, using: python -m PyInstaller --clean OptimizeSuper.spec
from pathlib import Path
project = Path(SPECPATH)
a = Analysis([str(project/'main.py')], pathex=[str(project)],
             binaries=[], datas=[(str(project/'assets'), 'assets')],
             hiddenimports=['psutil'], hookspath=[], hooksconfig={}, runtime_hooks=[],
             excludes=['PyQt5','PyQt6','PySide2','tkinter'], noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,a.binaries,a.datas,[],name='OptimizeSuper-MTDEV',
        debug=False,bootloader_ignore_signals=False,strip=False,upx=False,
        console=False,disable_windowed_traceback=False,
        icon=str(project/'assets/mtdev.ico'),uac_admin=False,
        version=str(project/'assets/version_info.txt'))
