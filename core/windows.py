"""Narrow Windows command gateway; no shell interpolation or PATH-based executables."""
from __future__ import annotations
import base64
import ctypes
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

IS_WINDOWS = sys.platform == 'win32'
class Unsupported(RuntimeError): pass

def require_windows():
    if not IS_WINDOWS:
        raise Unsupported('This operation requires Windows 10/11. Monitoring and file analysis remain available.')

def admin():
    return bool(IS_WINDOWS and ctypes.windll.shell32.IsUserAnAdmin())

def need_admin():
    require_windows()
    if not admin():
        raise PermissionError('Administrator permission required. Use Settings → Restart as administrator, then retry.')

def system_exe(name):
    require_windows()
    # These names are constants at call sites, never supplied by users.
    return str(Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32' / name)

def run(args, timeout=45):
    require_windows()
    result = subprocess.run([str(a) for a in args], capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=timeout,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        raise RuntimeError(f'Command failed ({result.returncode}): {(result.stderr or result.stdout).strip()}')
    return result.stdout.strip()

def powershell(script, timeout=45):
    prefix = "$ErrorActionPreference='Stop'; [Console]::OutputEncoding=[System.Text.UTF8Encoding]::new(); "
    encoded = base64.b64encode((prefix + script).encode('utf-16-le')).decode('ascii')
    return run([system_exe(r'WindowsPowerShell\v1.0\powershell.exe'), '-NoProfile',
                '-NonInteractive', '-EncodedCommand', encoded], timeout)

def ps_json(script, timeout=45):
    raw = powershell(script + ' | ConvertTo-Json -Depth 8 -Compress', timeout)
    return json.loads(raw) if raw else None

def quote(value):
    return "'" + str(value).replace("'", "''") + "'"

def elevate():
    require_windows()
    args = sys.argv[1:] if getattr(sys, 'frozen', False) else [str(Path(sys.argv[0]).resolve()), *sys.argv[1:]]
    args = [*args, '--mtdev-elevated-restart']
    execute=ctypes.windll.shell32.ShellExecuteW
    execute.argtypes=[ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_int]
    execute.restype=ctypes.c_void_p
    code = execute(None, 'runas', sys.executable,
                subprocess.list2cmdline(args), str(Path.cwd()), 1) or 0
    if code <= 32:
        raise RuntimeError('Elevation cancelled or Windows could not launch the application.')

TOOLS = {
    'Disk Cleanup': ('exe', 'cleanmgr.exe'),
    'Windows Update': ('uri', 'ms-settings:windowsupdate'),
    'Device Manager': ('msc', 'devmgmt.msc'),
    'Task Manager': ('exe', 'Taskmgr.exe'),
    'Windows Security': ('uri', 'windowsdefender:'),
    'System Information': ('exe', 'msinfo32.exe'),
    'Power Options': ('power', 'powercfg.cpl'),
    'Network Settings': ('uri', 'ms-settings:network-status'),
    'System Restore': ('exe', 'rstrui.exe'),
    'Game Mode': ('uri', 'ms-settings:gaming-gamemode'),
    'GPU scheduling': ('uri', 'ms-settings:display-advancedgraphics'),
}
def open_tool(name):
    require_windows()
    kind, value = TOOLS[name]
    if kind == 'uri':
        os.startfile(value)
    else:
        args = [system_exe('mmc.exe'), system_exe(value)] if kind == 'msc' else (
            [system_exe('control.exe'), value] if kind == 'power' else [system_exe(value)])
        subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    return f'Opened {name}. Windows controls any subsequent actions.'

def machine_info():
    result = {'os': platform.platform(), 'architecture': platform.machine(),
              'cpu': platform.processor() or platform.machine(), 'gpu': 'Unavailable'}
    if IS_WINDOWS:
        try:
            info = ps_json("[pscustomobject]@{ CPU=(Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name); GPU=(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name); OS=(Get-CimInstance Win32_OperatingSystem | Select-Object -ExpandProperty Caption) }")
            result.update(cpu=str(info['CPU']), gpu=str(info['GPU']), os=info['OS'])
        except Exception as e:
            result['hardware_note'] = str(e)
    return result
