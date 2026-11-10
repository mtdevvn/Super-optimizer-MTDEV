"""Process sampling and conservative, identity-checked termination."""
import ctypes
import os
from pathlib import Path
import psutil
from core import windows as win

BLOCKED = {'system','registry','idle','secure system','system idle process', 'smss.exe',
 'csrss.exe','wininit.exe','services.exe','lsass.exe','winlogon.exe','svchost.exe',
 'fontdrvhost.exe','dwm.exe','explorer.exe','sihost.exe','taskhostw.exe',
 'securityhealthservice.exe','msmpeng.exe','nissrv.exe','audiodg.exe','memory compression'}

class Processes:
    def __init__(self):
        self.cache = {}
    def sample(self):
        rows, fresh = [], {}
        for p in psutil.process_iter(['pid','name','username','exe','create_time','memory_info']):
            try:
                key = (p.pid, p.info['create_time'])
                q = self.cache.get(key, p)
                cpu = q.cpu_percent(None)
                mem = p.info['memory_info']
                rows.append({'pid':p.pid, 'created':p.info['create_time'], 'name':p.info['name'] or '?',
                             'cpu':cpu, 'ram':mem.rss if mem else 0,
                             'user':p.info['username'] or '', 'exe':p.info['exe'] or ''})
                fresh[key] = q
            except (psutil.Error, OSError):
                continue
        self.cache = fresh
        return rows

    @staticmethod
    def validate(pid, created):
        win.require_windows()
        p = psutil.Process(int(pid))
        if abs(p.create_time() - float(created)) > .01:
            raise RuntimeError('Process identity changed; refresh and select again.')
        own = psutil.Process()
        parents = {x.pid for x in own.parents()} | {own.pid}
        if p.pid in parents or p.pid <= 4 or p.name().lower() in BLOCKED:
            raise PermissionError('Protected or application-owned process cannot be closed.')
        if p.username().casefold() != own.username().casefold():
            raise PermissionError('Only processes owned by your current Windows account can be closed.')
        exe = Path(p.exe()).resolve()
        windir = Path(os.environ.get('SystemRoot', r'C:\Windows')).resolve()
        if exe.is_relative_to(windir):
            raise PermissionError('Executables inside the Windows directory are protected.')
        session = ctypes.c_ulong()
        if not ctypes.windll.kernel32.ProcessIdToSessionId(p.pid, ctypes.byref(session)) or session.value == 0:
            raise PermissionError('Service or unknown Windows session is protected.')
        # Ask Windows as well: reject protected processes even outside SystemRoot.
        k32 = ctypes.WinDLL('kernel32', use_last_error=True)
        k32.OpenProcess.restype = ctypes.c_void_p
        k32.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        handle = k32.OpenProcess(0x1000, False, p.pid)
        if not handle:
            raise PermissionError('Cannot verify process protection; refusing termination.')
        try:
            level = ctypes.c_ulong()
            k32.GetProcessInformation.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_ulong]
            if not k32.GetProcessInformation(handle, 7, ctypes.byref(level), ctypes.sizeof(level)) or level.value != 0xFFFFFFFE:
                raise PermissionError('Windows reports protected or unverifiable process protection.')
        finally:
            k32.CloseHandle.argtypes = [ctypes.c_void_p]
            k32.CloseHandle(handle)
        return p

    def terminate(self, row, store):
        p = self.validate(row['pid'], row['created'])
        entry = store.record('process_close', before={'pid':p.pid,'name':p.name()}, detail='User confirmed; unsaved work may be lost. Not reversible.')
        try:
            # Revalidate immediately before acting; psutil also checks PID reuse.
            self.validate(row['pid'], row['created']).terminate()
            p.wait(timeout=8)
            store.update(entry, status='completed')
            return f'Closed {row["name"]} ({row["pid"]}). No memory caches were emptied.'
        except Exception as e:
            store.update(entry, status='failed', detail=str(e))
            raise
