import os
from pathlib import Path
import shutil
from core import windows as win
from modules.settings_engine import RUN_KEY, reg_read
from modules.version_info import publisher

class Startup:
    def __init__(self,store): self.store=store
    def list(self):
        win.require_windows()
        import winreg as r
        result=[]
        for hive in ('HKEY_CURRENT_USER','HKEY_LOCAL_MACHINE'):
            for key in (RUN_KEY,r'Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run'):
                try:
                    with r.OpenKey(getattr(r,hive),key,0,r.KEY_READ|r.KEY_WOW64_64KEY) as h:
                        for i in range(r.QueryInfoKey(h)[1]):
                            name,value,typ=r.EnumValue(h,i)
                            result.append({'name':name,'command':str(value),'publisher':publisher(value),
                                           'location':hive+'\\'+key,'hive':hive,'key':key,'type':'registry'})
                except (FileNotFoundError, PermissionError): continue
        locations=[(Path(os.environ['APPDATA'])/'Microsoft/Windows/Start Menu/Programs/Startup',False),
                   (Path(os.environ['PROGRAMDATA'])/'Microsoft/Windows/Start Menu/Programs/Startup',True)]
        for folder,all_users in locations:
            if folder.is_dir():
                for p in folder.iterdir():
                    if p.is_file() and p.name.lower()!='desktop.ini':
                        result.append({'name':p.stem,'command':str(p),'publisher':'Unavailable',
                                       'location':str(folder),'type':'file','all_users':all_users})
        # Scheduled tasks and services remain under Windows' own management.
        return result
    def disable(self,row):
        name=(row['name']+' '+row['command']).casefold()
        if any(x in name for x in ('security','defender','antivirus','firewall','windows update','msmpeng','avp.exe','avast','avgui','mbam','norton','mcafee','eset','bitdefender')):
            raise PermissionError('Security-related startup entries are protected.')
        if row['type']=='registry':
            from modules.settings_engine import SettingsEngine
            return SettingsEngine(self.store).registry(row['hive'],row['key'],row['name'],None,'Disable startup: '+row['name'])
        if row.get('all_users'): win.need_admin()
        src=Path(row['command'])
        if src.is_symlink(): raise PermissionError('Redirected startup files are not modified.')
        import uuid
        dst=self.store.root/'backups'/(uuid.uuid4().hex+'_'+src.name)
        entry=self.store.record('startup_file',before={'source':str(src),'backup':str(dst),'all_users':row.get('all_users',False)},detail='Disable startup: '+row['name'])
        try:
            shutil.move(str(src),str(dst))
            self.store.update(entry,status='completed'); return 'Startup shortcut disabled. Restore it in Restore Center.'
        except Exception as e:
            self.store.update(entry,status='failed',detail=str(e)); raise
