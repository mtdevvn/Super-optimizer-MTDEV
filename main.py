"""OPTIMIZE SUPER | MTDEV entry point. Starts without administrator privileges."""
import os
from pathlib import Path
import sys

if __name__ == '__main__':
    from PySide6.QtCore import QLockFile
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication,QMessageBox
    from core.state import Store,data_root
    from ui.window import Window
    app=QApplication(sys.argv)
    app.setApplicationName('OPTIMIZE SUPER | MTDEV');app.setOrganizationName('MTDEV')
    app.setQuitOnLastWindowClosed(True)
    if sys.platform=='win32' and (sys.maxsize<=2**32 or sys.getwindowsversion().major<10):
        QMessageBox.critical(None,'Unsupported platform','Use Windows 10 or Windows 11 with 64-bit Python.');sys.exit(1)
    assets=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))/'assets'
    app.setWindowIcon(QIcon(str(assets/'mtdev.ico')))
    data_root().mkdir(parents=True,exist_ok=True)
    lock=QLockFile(str(data_root()/'instance.lock'));lock.setStaleLockTime(30000)
    if not lock.tryLock(15000 if '--mtdev-elevated-restart' in sys.argv else 100):
        QMessageBox.information(None,'Optimize Super','Another instance is running. Open it from the system tray.');sys.exit(1)
    try:
        store=Store()
        def exception_hook(typ,value,tb):
            import traceback
            detail=''.join(traceback.format_exception(typ,value,tb));store.logger.error(detail)
            QMessageBox.critical(None,'Unexpected error',detail[-5000:])
        sys.excepthook=exception_hook
        window=Window(store,assets);window.show()
        sys.exit(app.exec())
    except Exception as e:
        QMessageBox.critical(None,'Cannot start Optimize Super',f'{e}\nThe application did not reset your saved configuration. Review its files before retrying.')
        sys.exit(1)
