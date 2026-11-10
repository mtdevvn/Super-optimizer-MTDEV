"""Reversible settings. Persist the original state before every modification."""
from __future__ import annotations
import base64
import ctypes
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from core import windows as win

RUN_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'

def encode_value(value, kind):
    return {'type':kind, 'value':base64.b64encode(value).decode('ascii') if isinstance(value,bytes) else value,
            'binary':isinstance(value,bytes)}
def decode_value(item):
    return base64.b64decode(item['value']) if item.get('binary') else item['value']

def reg_read(hive, key, name):
    win.require_windows()
    import winreg as r
    try:
        with r.OpenKey(getattr(r,hive),key,0,r.KEY_READ|r.KEY_WOW64_64KEY) as h:
            v,t=r.QueryValueEx(h,name)
            return encode_value(v,t)
    except FileNotFoundError: return None

def reg_write(hive,key,name,value):
    win.require_windows()
    import winreg as r
    if hive=='HKEY_LOCAL_MACHINE': win.need_admin()
    with r.CreateKeyEx(getattr(r,hive),key,0,r.KEY_SET_VALUE|r.KEY_WOW64_64KEY) as h:
        if value is None:
            try: r.DeleteValue(h,name)
            except FileNotFoundError: pass
        else: r.SetValueEx(h,name,0,value['type'],decode_value(value))

class SettingsEngine:
    def __init__(self,store): self.store=store
    def registry(self,hive,key,name,value,label):
        before={'hive':hive,'key':key,'name':name,'value':reg_read(hive,key,name)}
        entry=self.store.record('registry',before=before,after={'value':value},detail=label)
        try:
            reg_write(hive,key,name,value)
            if reg_read(hive,key,name)!=value: raise RuntimeError('Registry verification failed.')
            self.store.update(entry,status='completed')
            return label + ' applied. Original value saved in Restore Center.'
        except Exception as e:
            self.store.update(entry,status='failed',detail=f'{label}: {e}'); raise
    def game_mode(self):
        # One documented user preference only; no security or service changes.
        return self.registry('HKEY_CURRENT_USER',r'Software\Microsoft\GameBar','AutoGameModeEnabled',
                             encode_value(1,4),'Game Mode preference')
    def animation_state(self):
        win.require_windows()
        enabled=ctypes.c_int()
        if not ctypes.windll.user32.SystemParametersInfoW(0x1042,0,ctypes.byref(enabled),0):
            raise ctypes.WinError()
        return bool(enabled.value)
    def set_animation(self,enabled):
        win.require_windows()
        # SPI_SETCLIENTAREAANIMATION; public Windows API preserves unrelated preferences.
        if not ctypes.windll.user32.SystemParametersInfoW(0x1043,0,ctypes.c_void_p(int(enabled)),3):
            raise ctypes.WinError()
        if self.animation_state()!=enabled:
            raise RuntimeError('Windows animation preference verification failed.')
    def animation_setting(self):
        entry=self.store.record('animation',before={'enabled':self.animation_state()},
                                after={'enabled':False},detail='Disable client-area UI animation using Windows SystemParametersInfo')
        try:
            self.set_animation(False)
            self.store.update(entry,status='completed')
            return 'Windows client-area animations disabled and verified. Original preference backed up.'
        except Exception as e:
            self.store.update(entry,status='failed',detail=str(e));raise
    def self_startup(self,enabled):
        args = [sys.executable] if getattr(sys,'frozen',False) else [sys.executable,str(Path(sys.argv[0]).resolve())]
        return self.registry('HKEY_CURRENT_USER',RUN_KEY,'OptimizeSuperMTDEV',
                             encode_value(subprocess.list2cmdline(args),1) if enabled else None,
                             'Start Optimize Super with Windows' if enabled else 'Disable Optimize Super startup')
    def power_current(self):
        output=win.run([win.system_exe('powercfg.exe'),'/getactivescheme'])
        match=re.search(r'\b[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}\b',output)
        if not match: raise RuntimeError('Cannot determine current power plan.')
        return match.group(0)
    def power(self, balanced=False):
        win.require_windows()
        target='381b4222-f694-41f0-9685-ff5bb260df2e' if balanced else '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'
        listing=win.run([win.system_exe('powercfg.exe'),'/list'])
        if target not in listing.lower():
            raise win.Unsupported('This power plan is unavailable on this device (common on Modern Standby laptops). Use Windows Power Options.')
        before=self.power_current()
        entry=self.store.record('power',before={'guid':before},after={'guid':target},detail='Balanced' if balanced else 'High performance; increases heat and battery use')
        try:
            win.run([win.system_exe('powercfg.exe'),'/setactive',target])
            if self.power_current().lower()!=target: raise RuntimeError('Windows did not activate the requested power plan.')
            self.store.update(entry,status='completed'); return 'Power plan verified. Original plan saved in Restore Center.'
        except Exception as e:
            self.store.update(entry,status='failed',detail=str(e)); raise
    def restore_point(self):
        win.need_admin()
        entry=self.store.record('restore_point',detail='Windows System Protection checkpoint')
        try:
            before=win.ps_json('Get-ComputerRestorePoint | Select-Object -ExpandProperty SequenceNumber') or []
            if not isinstance(before,list): before=[before]
            win.powershell("Checkpoint-Computer -Description 'Optimize Super MTDEV' -RestorePointType MODIFY_SETTINGS",timeout=180)
            after=win.ps_json("Get-ComputerRestorePoint | Select-Object SequenceNumber,Description,CreationTime") or []
            if isinstance(after,dict): after=[after]
            new=[r for r in after if r['SequenceNumber'] not in before and r['Description']=='Optimize Super MTDEV']
            if not new: raise RuntimeError('Windows did not create a new restore point. System Protection may be disabled or the checkpoint frequency limit may apply.')
            self.store.update(entry,status='completed',after=new); return 'New Windows restore point verified.'
        except Exception as e:
            self.store.update(entry,status='failed',detail=str(e)); raise
    def undo(self,entry,force=False):
        if entry.get('undone'): raise ValueError('Already restored.')
        kind,before=entry['kind'],entry['before']
        def identity(item):
            b=item.get('before') or {}
            if item['kind']=='registry':return ('registry',b.get('hive'),b.get('key'),b.get('name'))
            if item['kind']=='dns':return ('dns',b.get('guid'))
            if item['kind']=='power':return ('power',)
            if item['kind']=='animation':return ('animation',)
            if item['kind']=='startup_file':return ('startup_file',b.get('source'))
            return None
        key=identity(entry)
        if key and any(not x.get('undone') and x['id']!=entry['id'] and x['time']>entry['time'] and identity(x)==key for x in self.store.history()):
            raise RuntimeError('Restore newer changes to this setting first.')
        if kind=='registry':
            current=reg_read(before['hive'],before['key'],before['name'])
            if not force and current not in (before['value'],entry['after']['value']):
                raise RuntimeError('Value changed outside the app. Restore refused to avoid overwriting newer settings.')
            reg_write(before['hive'],before['key'],before['name'],before['value'])
            if reg_read(before['hive'],before['key'],before['name'])!=before['value']: raise RuntimeError('Restore verification failed.')
        elif kind=='animation':
            if self.animation_state() not in (before['enabled'],entry['after']['enabled']):
                raise RuntimeError('Windows animation preference changed outside this app.')
            self.set_animation(before['enabled'])
        elif kind=='power':
            current=self.power_current().lower()
            if not force and current not in (entry['after']['guid'].lower(),before['guid'].lower()):
                raise RuntimeError('Power plan changed outside the app. Restore refused.')
            win.run([win.system_exe('powercfg.exe'),'/setactive',before['guid']])
            if self.power_current().lower()!=before['guid'].lower(): raise RuntimeError('Power plan restore verification failed.')
        elif kind=='startup_file':
            src,dst=Path(before['source']),Path(before['backup'])
            if src.exists(): raise FileExistsError('Original startup path is occupied. Restore refused.')
            if not dst.exists(): raise FileNotFoundError('Startup backup is missing.')
            if before.get('all_users'): win.need_admin()
            shutil.move(str(dst),str(src))
        elif kind=='dns':
            from modules.network import Network
            Network(self.store).restore(entry)
        else: raise ValueError('This action has no automatic undo. Cleanup and closed processes cannot be reversed.')
        self.store.update(entry,undone=True,detail=entry.get('detail','')+' | Original settings restored')
        return 'Original setting restored and verified.'
    def restore_defaults(self):
        # Undo newest first, keeping the chain of prior values intact. Never invent global Windows defaults.
        reports=[]
        for item in self.store.history():
            if not item.get('undone') and item['kind'] in {'registry','power','dns','startup_file','animation'}:
                try: reports.append(item['id']+': '+self.undo(item))
                except Exception as e: reports.append(item['id']+': FAILED: '+str(e))
        return '\n'.join(reports) or 'No supported changes to restore.'
