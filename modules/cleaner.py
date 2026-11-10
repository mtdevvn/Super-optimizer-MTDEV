"""Conservative cleanup. Scans return immutable identities, never wildcard deletions."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib
import os
from pathlib import Path
import stat
import time
import psutil
from core import windows as win

AGE_SECONDS = 48 * 3600
PROTECTED_SUFFIXES = {'.exe','.dll','.sys','.msi','.msp','.com','.bat','.cmd','.ps1','.lnk'}
BROWSERS = {'chrome.exe','msedge.exe','firefox.exe','brave.exe'}

def reparse(path):
    s = path.lstat()
    return stat.S_ISLNK(s.st_mode) or bool(getattr(s,'st_file_attributes',0) & 0x400)

def safe_chain(path, root):
    path, root = Path(path).absolute(), Path(root).absolute()
    if not path.is_relative_to(root) or path == root:
        return False
    try:
        # Include ancestors above the approved root: a redirected root must not escape policy.
        return not any(reparse(p) for p in (path,*path.parents))
    except OSError:
        return False

@dataclass(frozen=True)
class Candidate:
    path: str
    root: str
    category: str
    size: int
    mtime_ns: int
    device: int
    inode: int
    def identity(self):
        return self.device, self.inode, self.size, self.mtime_ns

class Cleaner:
    def __init__(self, roots=None):
        # Windows paths only: never use arbitrary TEMP environment paths as delete roots.
        local = Path(os.environ.get('LOCALAPPDATA', str(Path.home()/'AppData/Local')))
        windows = Path(os.environ.get('SystemRoot', r'C:\Windows'))
        self.roots = roots if roots is not None else {
            'User temporary files':[local/'Temp'],
            'Windows temporary files':[windows/'Temp'],
            'Application cache':[local/'D3DSCache'],
            'Thumbnail cache':[local/'Microsoft/Windows/Explorer'],
            'Browser cache':[local/'Google/Chrome/User Data/Default/Cache/Cache_Data',
                             local/'Microsoft/Edge/User Data/Default/Cache/Cache_Data']}
        self.notes = []
    @staticmethod
    def browser_running():
        # Inaccessible names are treated conservatively.
        for p in psutil.process_iter(['name']):
            try:
                if p.info['name'] is None or p.info['name'].lower() in BROWSERS:
                    return True
            except psutil.Error:
                return True
        return False
    def scan(self, categories, progress=lambda s:None, cancelled=lambda:False):
        files, seen = [], set()
        self.notes = []
        for category in categories:
            if category == 'Browser cache' and self.browser_running():
                self.notes.append('Browser cache skipped: close Chrome, Edge, Firefox and Brave first.')
                continue
            for root in self.roots.get(category, []):
                root = Path(root).absolute()
                if not root.is_dir():
                    continue
                progress(f'Scanning {root}')
                def onerror(error):
                    self.notes.append(str(error))
                for folder, dirs, names in os.walk(root, followlinks=False, onerror=onerror):
                    if cancelled():
                        return files
                    dirs[:] = [d for d in dirs if safe_chain(Path(folder)/d,root)]
                    for name in names:
                        p = Path(folder)/name
                        if str(p).casefold() in seen or not safe_chain(p,root):
                            continue
                        if category == 'Thumbnail cache' and not (name.startswith('thumbcache_') and p.suffix == '.db'):
                            continue
                        if p.suffix.lower() in PROTECTED_SUFFIXES:
                            continue
                        try:
                            s = p.lstat()
                            if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1 or time.time()-s.st_mtime < AGE_SECONDS:
                                continue
                            files.append(Candidate(str(p),str(root),category,s.st_size,s.st_mtime_ns,s.st_dev,s.st_ino))
                            seen.add(str(p).casefold())
                        except OSError as e:
                            self.notes.append(str(e))
        return files
    def delete(self, candidates, store, progress=lambda s:None, cancelled=lambda:False):
        entry = store.record('cleanup', before=[asdict(c) for c in candidates],
                             detail='Confirmed permanent deletion. Files cannot be restored by this app.')
        deleted, skipped, size = [], [], 0
        try:
            for i,c in enumerate(candidates):
                if cancelled():
                    skipped.append('Cancelled; remaining files were not deleted.')
                    break
                p, root = Path(c.path), Path(c.root)
                allowed = [Path(r).absolute() for r in self.roots.get(c.category,[])]
                if root not in allowed or not safe_chain(p,root):
                    skipped.append(c.path + ': path validation failed'); continue
                if c.category == 'Browser cache' and self.browser_running():
                    skipped.append(c.path + ': browser running'); continue
                try:
                    s = p.lstat()
                    if (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns) != c.identity() or s.st_nlink != 1:
                        skipped.append(c.path + ': changed since scan'); continue
                    if time.time()-s.st_mtime < AGE_SECONDS or p.suffix.lower() in PROTECTED_SUFFIXES:
                        skipped.append(c.path + ': protected or recent'); continue
                    if c.category == 'Thumbnail cache' and not (p.name.startswith('thumbcache_') and p.suffix == '.db'):
                        skipped.append(c.path + ': not a thumbnail cache'); continue
                    p.unlink()
                    deleted.append(c.path); size += c.size
                except OSError as e:
                    skipped.append(f'{p}: {e}')
                if i % 30 == 0:
                    progress(f'Cleanup {i+1}/{len(candidates)} • {size:,} bytes removed')
            result = {'deleted':deleted,'skipped':skipped,'bytes':size}
            store.update(entry,status='completed_with_skips' if skipped else 'completed',after=result)
            return result
        except Exception as e:
            store.update(entry,status='failed',after={'deleted':deleted,'skipped':skipped,'bytes':size},detail=str(e))
            raise

def analyze(root, duplicates=False, progress=lambda s:None, cancelled=lambda:False, min_size=100*1024**2):
    """Read-only scan; no link traversal, no automatic personal-file removal."""
    root = Path(root).absolute()
    if not root.is_dir() or reparse(root):
        raise ValueError('Choose an existing non-redirected directory.')
    rows, by_size, errors, count = [], {}, [], 0
    for folder, dirs, names in os.walk(root,followlinks=False,onerror=lambda e:errors.append(str(e))):
        if cancelled(): break
        dirs[:] = [d for d in dirs if safe_chain(Path(folder)/d,root)]
        for name in names:
            if cancelled(): break
            p = Path(folder)/name
            if not safe_chain(p,root): continue
            try:
                s = p.stat(follow_symlinks=False)
                if not stat.S_ISREG(s.st_mode): continue
                count += 1
                if duplicates:
                    if s.st_size: by_size.setdefault(s.st_size,[]).append((p,s))
                elif s.st_size >= min_size:
                    rows.append({'path':str(p),'size':s.st_size,'group':''})
            except OSError as e: errors.append(str(e))
            if count % 200 == 0: progress(f'Analyzed {count:,} files')
    if duplicates and not cancelled():
        for size, files in by_size.items():
            if len(files)<2: continue
            hashes = {}
            for p, before in files:
                if cancelled(): break
                try:
                    digest = hashlib.sha256()
                    with p.open('rb') as stream:
                        while True:
                            if cancelled(): break
                            chunk=stream.read(1024*1024)
                            if not chunk: break
                            digest.update(chunk)
                    after = p.stat()
                    if cancelled() or (before.st_size,before.st_mtime_ns,before.st_ino) != (after.st_size,after.st_mtime_ns,after.st_ino):
                        continue
                    hashes.setdefault(digest.hexdigest(),[]).append((p,before.st_dev,before.st_ino))
                    progress(f'Hashing {p.name}')
                except OSError as e: errors.append(str(e))
            for digest, group in hashes.items():
                # Hard links share physical bytes and are not duplicate savings.
                if len({(d,i) for _,d,i in group})>1:
                    rows.extend({'path':str(p),'size':size,'group':digest} for p,_,_ in group)
    return {'rows':sorted(rows,key=lambda r:r['size'],reverse=True),'errors':errors,'cancelled':cancelled()}

class SHQUERYRBINFO(__import__('ctypes').Structure):
    _fields_ = [('cbSize',__import__('ctypes').c_ulong),('i64Size',__import__('ctypes').c_longlong),('i64NumItems',__import__('ctypes').c_longlong)]

def recycle_info():
    win.require_windows()
    import ctypes
    info = SHQUERYRBINFO(); info.cbSize=ctypes.sizeof(info)
    hr = ctypes.windll.shell32.SHQueryRecycleBinW(None,ctypes.byref(info))
    if hr: raise OSError(f'Recycle Bin query failed: HRESULT {hr}')
    return {'path':r'All drives: $Recycle.Bin (current user)', 'bytes':info.i64Size,'items':info.i64NumItems}

def empty_recycle(store):
    import ctypes
    info = recycle_info()
    entry=store.record('recycle_bin',before=info,detail='User confirmed permanent deletion; cannot undo.')
    hr=ctypes.windll.shell32.SHEmptyRecycleBinW(None,None,0x1|0x2|0x4)
    if hr:
        store.update(entry,status='failed',detail=f'HRESULT {hr}'); raise OSError(f'Recycle Bin failed: HRESULT {hr}')
    store.update(entry,status='completed',after=recycle_info())
    return 'Recycle Bin emptied. This action cannot be undone.'
