"""Read-only DirectX diagnostics. Never infer support from a registry toggle."""
from pathlib import Path
import re
import tempfile
import time
from core import windows as win

def parse_diagnostics(text):
    rows=[];adapter='Display adapter'
    for line in text.splitlines():
        stripped=line.strip()
        if stripped.lower().startswith('card name:'):adapter=stripped.split(':',1)[1].strip()
        if 'hardware scheduling:' in stripped.lower():
            data=stripped.split(':',1)[1].strip()
            support=re.search(r'(?<!\w)Supported\s*:\s*(True|False)',data,re.I)
            driver=re.search(r'DriverSupportState\s*:\s*(\w+)',data,re.I)
            enabled=re.search(r'(?<!\w)Enabled\s*:\s*(True|False)',data,re.I)
            if support:state='Supported' if support.group(1).lower()=='true' else 'Not supported'
            elif driver and driver.group(1).lower()=='stable':state='Driver reports stable support'
            elif driver and driver.group(1).lower()=='alwaysoff':state='Driver reports unavailable'
            else:state='Unknown — inspect Windows graphics settings'
            rows.append({'adapter':adapter,'support':state,'enabled':enabled.group(1) if enabled else 'Unknown','reported':data})
    return rows

def scheduling_check(store,progress=lambda s:None,cancelled=lambda:False):
    win.require_windows()
    progress('Reading DirectX hardware scheduling diagnostics…')
    with tempfile.TemporaryDirectory(prefix='dxdiag-',dir=store.root/'data') as folder:
        output=Path(folder)/'dxdiag.txt'
        win.run([win.system_exe('dxdiag.exe'),'/whql:off','/t',str(output)],timeout=90)
        # dxdiag may exit after starting another process; wait for a stable complete report.
        deadline=time.monotonic()+20;previous=None
        while time.monotonic()<deadline:
            if cancelled():return {'cancelled':True,'adapters':[]}
            if output.exists():
                size=output.stat().st_size
                if size and size==previous:break
                previous=size
            time.sleep(.25)
        if not output.exists():raise RuntimeError('DirectX did not produce a diagnostic report. Open Windows graphics settings.')
        raw=output.read_bytes()
        if raw.startswith((b'\xff\xfe',b'\xfe\xff')):text=raw.decode('utf-16',errors='replace')
        elif raw[:100].count(b'\x00')>10:text=raw.decode('utf-16-le',errors='replace')
        else:text=raw.decode('utf-8',errors='replace')
        rows=parse_diagnostics(text)
        return {'adapters':rows,'note':'Reported by DirectX; no settings were changed.' if rows else 'Automatic result unavailable (possibly localized or older DirectX output). Open GPU scheduling availability in Windows Settings to check.'}
