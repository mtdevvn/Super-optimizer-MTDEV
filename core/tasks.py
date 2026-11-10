import threading
import traceback
from PySide6.QtCore import QObject, QRunnable, Signal, QThread
from core.monitor import Monitor

class Signals(QObject):
    progress=Signal(str)
    result=Signal(object)
    error=Signal(str)
    finished=Signal()

class Job(QRunnable):
    def __init__(self,fn):
        super().__init__(); self.fn=fn; self.signals=Signals(); self.cancel=threading.Event()
    def run(self):
        try: self.signals.result.emit(self.fn(self.signals.progress.emit,self.cancel.is_set))
        except Exception: self.signals.error.emit(traceback.format_exc())
        finally: self.signals.finished.emit()

class MonitorThread(QThread):
    sample_ready=Signal(dict)
    failed=Signal(str)
    def run(self):
        monitor=Monitor()
        while not self.isInterruptionRequested():
            try: self.sample_ready.emit(monitor.sample())
            except Exception: self.failed.emit(traceback.format_exc())
            # Responsive shutdown; no forced QThread termination.
            for _ in range(10):
                if self.isInterruptionRequested(): return
                self.msleep(100)
