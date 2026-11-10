"""IPv4 DNS changes with exact static/DHCP provenance, no IPv6 rewrites."""
import ipaddress
import psutil
from core import windows as win
from modules.settings_engine import reg_read

PROFILES={'Cloudflare':['1.1.1.1','1.0.0.1'], 'Google':['8.8.8.8','8.8.4.4']}
class Network:
    def __init__(self,store): self.store=store
    def info(self):
        stats=psutil.net_if_stats(); result=[]
        for name, addresses in psutil.net_if_addrs().items():
            s=stats.get(name)
            result.append({'name':name,'up':bool(s and s.isup),'speed_mbps':s.speed if s else None,
                           'addresses':[a.address for a in addresses]})
        return result
    def adapters(self):
        rows=win.ps_json('Get-NetAdapter -Physical | Select-Object Name,InterfaceIndex,InterfaceGuid,Status') or []
        return [rows] if isinstance(rows,dict) else rows
    def snapshot(self,adapter):
        index=int(adapter['InterfaceIndex'])
        guid=str(adapter['InterfaceGuid']).strip('{}')
        import uuid
        uuid.UUID(guid)
        key=r'SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\{'+guid+'}'
        ns=reg_read('HKEY_LOCAL_MACHINE',key,'NameServer')
        manual=bool(ns and str(ns['value']).strip())
        servers=win.ps_json(f'Get-DnsClientServerAddress -InterfaceIndex {index} -AddressFamily IPv4 | Select-Object -ExpandProperty ServerAddresses') or []
        if isinstance(servers,str): servers=[servers]
        for ip in servers: ipaddress.IPv4Address(ip)
        if manual and not servers: raise RuntimeError('Static DNS could not be read. Refusing change without a valid backup.')
        return {'guid':guid,'index':index,'name':adapter['Name'],'manual':manual,'servers':servers}
    def resolve(self,guid):
        return next((a for a in self.adapters() if str(a['InterfaceGuid']).strip('{}').lower()==guid.lower()),None)
    def set_servers(self,adapter,servers):
        # Set-DnsClientServerAddress with explicit addresses scopes changes to IPv4.
        # ResetServerAddresses can affect both families; use netsh ipv4 for DHCP restore instead.
        if servers is None:
            win.run([win.system_exe('netsh.exe'),'interface','ipv4','set','dnsservers',
                     f'name={int(adapter["InterfaceIndex"])}','source=dhcp'])
        else:
            for ip in servers: ipaddress.IPv4Address(ip)
            ips=','.join(win.quote(ip) for ip in servers)
            win.powershell(f'Set-DnsClientServerAddress -InterfaceIndex {int(adapter["InterfaceIndex"])} -ServerAddresses @({ips})')
    def apply(self,adapter,profile):
        win.need_admin()
        before=self.snapshot(adapter); servers=PROFILES[profile]
        entry=self.store.record('dns',before=before,after={'servers':servers},detail=profile+' IPv4 DNS')
        try:
            self.set_servers(adapter,servers)
            actual=self.snapshot(adapter)
            if actual['servers']!=servers or not actual['manual']: raise RuntimeError('DNS verification failed; use Restore Center to recover saved configuration.')
            self.store.update(entry,status='completed'); return 'IPv4 DNS updated and verified. This does not guarantee lower gaming ping.'
        except Exception as e:
            self.store.update(entry,status='failed',detail=str(e)); raise
    def restore(self,entry):
        win.need_admin()
        before=entry['before']; adapter=self.resolve(before['guid'])
        if not adapter: raise RuntimeError('Original network adapter is unavailable.')
        current=self.snapshot(adapter)
        original=(before['manual'],before['servers'] if before['manual'] else None)
        active=(current['manual'],current['servers'] if current['manual'] else None)
        if active not in (original,(True,entry['after']['servers'])):
            raise RuntimeError('DNS changed outside this app. Restore refused.')
        self.set_servers(adapter,before['servers'] if before['manual'] else None)
        actual=self.snapshot(adapter)
        if actual['manual']!=before['manual'] or (before['manual'] and actual['servers']!=before['servers']):
            raise RuntimeError('DNS restore verification failed.')
    def flush(self):
        win.require_windows()
        entry=self.store.record('dns_flush',detail='Flush Windows resolver cache; no configuration change')
        try:
            output=win.run([win.system_exe('ipconfig.exe'),'/flushdns'])
            self.store.update(entry,status='completed',after={'output':output}); return output
        except Exception as e:
            self.store.update(entry,status='failed',detail=str(e)); raise
