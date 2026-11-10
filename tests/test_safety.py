import json
import os
from pathlib import Path
import time
import pytest
from core.state import Store
from modules.cleaner import Cleaner,analyze
from modules.settings_engine import SettingsEngine,encode_value
from core import windows as win

@pytest.fixture
def store(tmp_path):return Store(tmp_path/'state')

def old_file(root,name,content=b'old cache'):
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(content)
    before=time.time()-72*3600;os.utime(p,(before,before));return p

def test_cleanup_preview_is_read_only_and_requires_same_file(tmp_path,store):
    root=tmp_path/'Temp';p=old_file(root,'cache.tmp'); cleaner=Cleaner({'test':[root]})
    files=cleaner.scan(['test']);assert p.exists() and len(files)==1
    p.write_bytes(b'new content after preview')
    result=cleaner.delete(files,store)
    assert result['bytes']==0 and p.exists() and result['skipped']

def test_cleanup_only_approved_old_regular_files(tmp_path,store):
    root=tmp_path/'Temp';old=old_file(root,'old.tmp');protected=old_file(root,'driver.sys')
    fresh=root/'fresh.tmp';fresh.write_text('active')
    outside=old_file(tmp_path/'personal','photo.jpg')
    cleaner=Cleaner({'test':[root]});files=cleaner.scan(['test'])
    assert [f.path for f in files]==[str(old)]
    result=cleaner.delete(files,store)
    assert result['bytes']==9 and not old.exists()
    assert protected.exists() and fresh.exists() and outside.exists()
    history=store.history();assert history[0]['before'][0]['path']==str(old)
    assert history[0]['status']=='completed'

def test_links_and_hardlinks_are_not_cleanup_candidates(tmp_path):
    root=tmp_path/'Temp';root.mkdir();target=old_file(tmp_path/'personal','target.txt')
    try:
        (root/'shortcut').symlink_to(target)
        (root/'junction').symlink_to(target.parent,target_is_directory=True)
    except OSError:pytest.skip('Symlink creation unavailable (Windows Developer Mode or admin required)')
    os.link(target,root/'hardlink.tmp')
    assert Cleaner({'test':[root]}).scan(['test'])==[]

def test_cleanup_cancel_preserves_files(tmp_path,store):
    root=tmp_path/'Temp';p=old_file(root,'keep.tmp');cl=Cleaner({'test':[root]})
    result=cl.delete(cl.scan(['test']),store,cancelled=lambda:True)
    assert p.exists() and result['bytes']==0

def test_duplicate_scan_hashes_content_without_deleting(tmp_path):
    root=tmp_path/'files';a=old_file(root,'a.txt',b'same');b=old_file(root,'b.txt',b'same');c=old_file(root,'c.txt',b'diff')
    result=analyze(root,duplicates=True)
    assert {r['path'] for r in result['rows']}=={str(a),str(b)}
    assert all(p.exists() for p in [a,b,c])

def test_state_persists_original_before_mutation(store,monkeypatch):
    value=encode_value('original',1)
    monkeypatch.setattr('modules.settings_engine.reg_read',lambda *a:value)
    def fail(*args):
        history=store.history();assert history[0]['status']=='prepared'
        assert history[0]['before']['value']==value
        raise PermissionError('denied')
    monkeypatch.setattr('modules.settings_engine.reg_write',fail)
    with pytest.raises(PermissionError):SettingsEngine(store).registry('HKEY_CURRENT_USER','key','name',None,'test')
    assert store.history()[0]['status']=='failed'
    assert store.history()[0]['before']['value']==value

def test_registry_undo_preserves_type_and_external_changes(store,monkeypatch):
    state={'value':encode_value(b'abc',3)};before=state['value']
    monkeypatch.setattr('modules.settings_engine.reg_read',lambda *a:state['value'])
    monkeypatch.setattr('modules.settings_engine.reg_write',lambda *a:state.update(value=a[-1]))
    eng=SettingsEngine(store);eng.registry('HKEY_CURRENT_USER','key','name',encode_value(2,4),'test')
    entry=store.history()[0];state['value']=encode_value(99,4)
    with pytest.raises(RuntimeError,match='outside'):eng.undo(entry)
    state['value']=encode_value(2,4);eng.undo(entry)
    assert state['value']==before and store.history()[0]['undone']

def test_restore_chain_refuses_out_of_order(store,monkeypatch):
    state={'value':encode_value(0,4)}
    monkeypatch.setattr('modules.settings_engine.reg_read',lambda *a:state['value'])
    monkeypatch.setattr('modules.settings_engine.reg_write',lambda *a:state.update(value=a[-1]))
    eng=SettingsEngine(store)
    eng.registry('HKEY_CURRENT_USER','key','name',encode_value(1,4),'first');first=store.history()[0]
    eng.registry('HKEY_CURRENT_USER','key','name',encode_value(2,4),'second')
    with pytest.raises(RuntimeError,match='newer'):eng.undo(first)
    report=eng.restore_defaults();assert 'FAILED' not in report and state['value']==encode_value(0,4)

def test_corrupt_preferences_are_not_silently_overwritten(tmp_path):
    path=tmp_path/'config/settings.json';path.parent.mkdir();path.write_text('broken')
    with pytest.raises(json.JSONDecodeError):Store(tmp_path)
    assert path.read_text()=='broken'

def test_dns_change_failure_keeps_recoverable_backup(store,monkeypatch):
    from modules.network import Network
    monkeypatch.setattr(win,'need_admin',lambda:None)
    net=Network(store);original={'guid':'test','index':1,'name':'LAN','manual':False,'servers':['192.168.1.1']}
    monkeypatch.setattr(net,'snapshot',lambda a:dict(original))
    def failure(*a):
        assert store.history()[0]['before']==original
        raise RuntimeError('command denied')
    monkeypatch.setattr(net,'set_servers',failure)
    with pytest.raises(RuntimeError):net.apply({'InterfaceIndex':1},'Cloudflare')
    assert store.history()[0]['status']=='failed'

def test_dns_external_dhcp_change_is_not_overwritten(store,monkeypatch):
    from modules.network import Network
    monkeypatch.setattr(win,'need_admin',lambda:None)
    net=Network(store);monkeypatch.setattr(net,'resolve',lambda a:{'InterfaceIndex':1})
    monkeypatch.setattr(net,'snapshot',lambda a:{'manual':False,'servers':['10.0.0.1']})
    monkeypatch.setattr(net,'set_servers',lambda *a:pytest.fail('must not mutate external settings'))
    entry={'before':{'guid':'g','manual':True,'servers':['9.9.9.9']},'after':{'servers':['1.1.1.1']}}
    with pytest.raises(RuntimeError,match='outside'):net.restore(entry)

def test_non_windows_mutations_are_explicitly_unsupported():
    if win.IS_WINDOWS:pytest.skip('non-Windows guard')
    with pytest.raises(win.Unsupported):win.powershell('Get-Date')

def test_visual_preference_is_backed_up_verified_and_reversible(store,monkeypatch):
    state={'enabled':True};eng=SettingsEngine(store)
    monkeypatch.setattr(eng,'animation_state',lambda:state['enabled'])
    def apply(enabled):
        assert store.history()[0]['before']=={'enabled':True}
        state['enabled']=enabled
    monkeypatch.setattr(eng,'set_animation',apply)
    eng.animation_setting();assert not state['enabled']
    eng.undo(store.history()[0]);assert state['enabled']

def test_replacing_cleanup_parent_with_symlink_cannot_delete_personal_data(tmp_path,store):
    root=tmp_path/'Temp';p=old_file(root/'child','cache.tmp')
    cl=Cleaner({'test':[root]});files=cl.scan(['test'])
    personal=tmp_path/'personal';target=old_file(personal,'cache.tmp',b'precious')
    p.unlink();p.parent.rmdir()
    try:p.parent.symlink_to(personal,target_is_directory=True)
    except OSError:pytest.skip('Symlink creation unavailable')
    result=cl.delete(files,store)
    assert target.exists() and result['bytes']==0 and result['skipped']

def test_dxdiag_parser_reports_only_explicit_hardware_scheduling_values():
    from modules.gaming import parse_diagnostics
    rows=parse_diagnostics('Card name: GPU A\n Hardware Scheduling: DriverSupportState:Stable Enabled:True\nCard name: GPU B\n Hardware Scheduling: Supported:False Enabled:False')
    assert rows[0]['support']=='Driver reports stable support' and rows[0]['enabled']=='True'
    assert rows[1]['support']=='Not supported'
    assert parse_diagnostics('No hardware data')==[]

def test_critical_processes_blocked_without_termination(monkeypatch):
    from types import SimpleNamespace
    import modules.processes as module
    monkeypatch.setattr(win,'require_windows',lambda:None)
    own=SimpleNamespace(pid=500,parents=lambda:[])
    for pid,name in [(4,'System'),(100,'svchost.exe'),(101,'MsMpEng.exe'),(102,'explorer.exe')]:
        target=SimpleNamespace(pid=pid,create_time=lambda:10.0,name=lambda:name)
        monkeypatch.setattr(module.psutil,'Process',lambda pid=None,t=target:t if pid is not None else own)
        with pytest.raises(PermissionError):module.Processes.validate(pid,10.0)

def test_pid_reuse_blocks_process_close(monkeypatch):
    from types import SimpleNamespace
    import modules.processes as module
    monkeypatch.setattr(win,'require_windows',lambda:None)
    monkeypatch.setattr(module.psutil,'Process',lambda pid:SimpleNamespace(create_time=lambda:200))
    with pytest.raises(RuntimeError,match='identity'):module.Processes.validate(123,100)

def test_default_settings_are_independent(tmp_path):
    a=Store(tmp_path/'a');b=Store(tmp_path/'b')
    a.settings['games'].append({'name':'local test'})
    assert b.settings['games']==[]
