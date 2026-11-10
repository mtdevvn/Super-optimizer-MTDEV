"""Offscreen Qt integration test; never invokes Windows mutations."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
import time
from PySide6.QtWidgets import QApplication
from core.state import Store
from ui.window import Window

APP=QApplication.instance() or QApplication([])

def pump_until(predicate,timeout=10):
    deadline=time.monotonic()+timeout
    while not predicate() and time.monotonic()<deadline:
        APP.processEvents();time.sleep(.01)
    assert predicate()

def test_all_pages_themes_and_worker_lifecycle(tmp_path,monkeypatch):
    from core import windows as win
    store=Store(tmp_path/'state');store.settings['animations']=False
    w=Window(store,Path(__file__).parents[1]/'assets')
    errors=[];w.error=lambda text:errors.append(text)
    w.show()
    try:
        pump_until(lambda:w.finished_jobs>=1 and bool(w.snapshot))
        for theme in ['Light','Dark']:
            store.settings['theme']=theme;w.apply_personalization()
            for page in range(11):
                w.navigate(page);APP.processEvents()
                assert w.stack.currentIndex()==page
        store.settings['language']='Tiếng Việt';w.apply_personalization()
        assert 'Tổng quan' in w.nav[0].text()
        store.settings['language']='English';w.apply_personalization()
        assert w.cpu.value.text()!='—' and w.ram_table.rowCount()>0
        assert w.process_table.rowCount()>0
        w.navigate(6)
        w.search.setText('__not_a_real_process__');assert w.process_table.rowCount()==0
        w.search.clear();assert w.process_table.rowCount()>0
        assert w.disks.rowCount()>0
        w.start_job(lambda p,c: {'working':True},lambda result:errors.append('wrong') if not result['working'] else None,report=False)
        pump_until(lambda:w.job is None)
        assert not errors
        out=os.environ.get('MTDEV_SCREENSHOT_DIR')
        if out:
            folder=Path(out);folder.mkdir(parents=True,exist_ok=True)
            w.navigate(0);pump_until(lambda:len(w.cpu.graph.values)>=3);APP.processEvents();w.grab().save(str(folder/'dashboard-dark.png'))
            w.navigate(1);APP.processEvents();w.grab().save(str(folder/'optimization-dark.png'))
            store.settings['theme']='Light';w.apply_personalization();w.navigate(6);APP.processEvents();w.grab().save(str(folder/'processes-light.png'))
    finally:
        w.exit_requested=True;w.close();APP.processEvents()
        assert not w.monitor.isRunning()
