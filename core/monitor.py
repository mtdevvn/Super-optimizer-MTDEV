import os
from pathlib import Path
import subprocess
import time
import psutil
from modules.processes import Processes
from core import windows as win

class Monitor:
    def __init__(self):
        self.processes = Processes()
        self.last_net = psutil.net_io_counters()
        self.last_time = time.monotonic()
        self.gpu = {'usage':None,'temp':None,'note':'GPU sensors unavailable; vendor support is required.'}
        self.next_gpu = 0
    def gpu_read(self):
        if not win.IS_WINDOWS:
            return
        candidates = [Path(os.environ.get('SystemRoot', r'C:\Windows'))/'System32/nvidia-smi.exe',
                      Path(os.environ.get('ProgramW6432', r'C:\Program Files'))/'NVIDIA Corporation/NVSMI/nvidia-smi.exe']
        executable = next((p for p in candidates if p.is_file()), None)
        if executable:
            try:
                raw = win.run([executable, '--query-gpu=name,utilization.gpu,temperature.gpu', '--format=csv,noheader,nounits'], timeout=3)
                vals = raw.splitlines()[0].rsplit(',',2)
                self.gpu = {'name':vals[0], 'usage':float(vals[1]), 'temp':float(vals[2]), 'note':'NVIDIA device 0; vendor sensor'}
            except (ValueError, OSError, RuntimeError, subprocess.SubprocessError):
                self.gpu = {'usage':None,'temp':None,'note':'GPU sensors unavailable or unsupported driver.'}
    def sample(self):
        now = time.monotonic()
        if now >= self.next_gpu:
            self.gpu_read()
            self.next_gpu = now + 10
        net = psutil.net_io_counters()
        dt = max(now-self.last_time, .001)
        up = max(0,net.bytes_sent-self.last_net.bytes_sent)/dt
        down = max(0,net.bytes_recv-self.last_net.bytes_recv)/dt
        self.last_net, self.last_time = net, now
        ram = psutil.virtual_memory()
        disks = []
        for p in psutil.disk_partitions():
            if 'cdrom' in p.opts or not p.fstype:
                continue
            try:
                d = psutil.disk_usage(p.mountpoint)
                disks.append({'path':p.mountpoint,'total':d.total,'used':d.used,'percent':d.percent})
            except (OSError, PermissionError):
                continue
        if not disks:
            # Containers may hide partition metadata. Still report the real filesystem usage.
            root_path = str(Path.home().anchor or '/')
            try:
                d=psutil.disk_usage(root_path)
                disks.append({'path':root_path,'total':d.total,'used':d.used,'percent':d.percent})
            except OSError:
                pass
        temps = []
        try:
            for key, entries in psutil.sensors_temperatures().items():
                if any(x in key.lower() for x in ('coretemp','k10temp','cpu')):
                    temps.extend(t.current for t in entries if t.current is not None)
        except (AttributeError, OSError):
            pass
        return {'cpu':psutil.cpu_percent(), 'cpu_temp':max(temps) if temps else None,
                'ram_percent':ram.percent,'ram_used':ram.used,'ram_total':ram.total,
                'ram_available':ram.available,'up':up,'down':down,'gpu':dict(self.gpu),
                'disks':disks,'uptime':max(0,time.time()-psutil.boot_time()),
                'processes':self.processes.sample()}
