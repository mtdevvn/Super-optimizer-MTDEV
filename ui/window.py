from __future__ import annotations
import json
from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys
import time
from PySide6.QtCore import Qt, QTimer, QThreadPool, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QFrame,QVBoxLayout,QHBoxLayout,
 QGridLayout,QPushButton,QLabel,QStackedWidget,QScrollArea,QLineEdit,QComboBox,QCheckBox,
 QSpinBox,QPlainTextEdit,QMessageBox,QFileDialog,QSystemTrayIcon,QMenu,QProgressBar,
 QGraphicsOpacityEffect,QDialog)
from core import windows as win
from core.tasks import Job, MonitorThread
from core.state import DEFAULTS
from modules.cleaner import Cleaner,Candidate,analyze,recycle_info,empty_recycle
from modules.settings_engine import SettingsEngine,reg_read,RUN_KEY
from modules.startup import Startup
from modules.network import Network,PROFILES
from modules.processes import Processes
from ui.widgets import label,card,Metric,Table,CleanupReview,fmt
from ui.theme import stylesheet

NAV = ['Dashboard','Super Optimize','Gaming Boost','RAM Management','Storage Cleaner',
       'Startup Manager','Process Manager','Network','Windows Tools','Restore Center','Settings']
VI = dict(zip(NAV,['Tổng quan','Tối ưu hệ thống','Tối ưu chơi game','Quản lý RAM','Dọn dẹp ổ đĩa',
 'Khởi động cùng Windows','Quản lý tiến trình','Mạng','Công cụ Windows','Khôi phục & sao lưu','Cài đặt']))

class Window(QMainWindow):
    def __init__(self,store,assets):
        super().__init__(); self.store=store; self.assets=Path(assets)
        self.engine=SettingsEngine(store); self.cleaner=Cleaner(); self.startup=Startup(store); self.network=Network(store)
        self.snapshot={}; self.job=None; self.pending_result=None; self.pool=QThreadPool(self); self.pool.setMaxThreadCount(1)
        self.last_cleanup=time.monotonic(); self.last_table=0; self.exit_requested=False
        self.setWindowTitle('OPTIMIZE SUPER | MTDEV'); self.setWindowIcon(QIcon(str(self.assets/'mtdev.ico')))
        self.resize(1280,860); self.setMinimumSize(920,650)
        self.shell=QWidget(); self.shell.setObjectName('shell'); self.setCentralWidget(self.shell)
        root=QHBoxLayout(self.shell); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        sidebar=QFrame(); self.sidebar=sidebar; sidebar.setObjectName('sidebar'); sidebar.setFixedWidth(211)
        side=QVBoxLayout(sidebar); side.setContentsMargins(16,26,16,20); side.setSpacing(5)
        side.addWidget(label('◈  MTDEV','brand')); side.addWidget(label('OPTIMIZE SUPER','eyebrow')); side.addSpacing(25)
        self.nav=[]
        for index,title in enumerate(NAV):
            b=QPushButton(f'{index+1:02}   {title}'); b.setObjectName('nav'); b.setCheckable(True)
            b.clicked.connect(lambda checked=False,i=index:self.navigate(i)); side.addWidget(b); self.nav.append(b)
        side.addStretch(); side.addWidget(label('LOCAL ENGINE  /  v1.0.0','eyebrow'))
        self.priv=label('● Administrator' if win.admin() else '● Standard user','muted'); side.addWidget(self.priv)
        root.addWidget(sidebar)
        main=QVBoxLayout(); main.setContentsMargins(25,22,25,18); main.setSpacing(14); root.addLayout(main,1)
        header=QHBoxLayout(); self.heading=label('Dashboard','title'); header.addWidget(self.heading); header.addStretch()
        self.live=label('●  LIVE SYSTEM DATA','eyebrow'); self.live.setWordWrap(False); header.addWidget(self.live); main.addLayout(header)
        self.subtitle=label('Performance, with control. Every change has a record.','muted'); main.addWidget(self.subtitle)
        self.stack=QStackedWidget(); main.addWidget(self.stack,1)
        self.builders=[self.dashboard_page,self.optimize_page,self.gaming_page,self.ram_page,self.cleaner_page,
                       self.startup_page,self.process_page,self.network_page,self.tools_page,self.restore_page,self.settings_page]
        for builder in self.builders:
            area=QScrollArea(); area.setWidgetResizable(True); area.setFrameShape(QFrame.NoFrame)
            content=QWidget(); box=QVBoxLayout(content); box.setContentsMargins(1,1,10,8); box.setSpacing(16)
            builder(box); box.addStretch(); area.setWidget(content); self.stack.addWidget(area)
        footer=QHBoxLayout(); self.status=label('Ready • No changes applied','muted'); footer.addWidget(self.status,1)
        self.cancel_button=QPushButton('Cancel scan'); self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self.cancel_job); footer.addWidget(self.cancel_button)
        main.addLayout(footer)
        self.progress=QProgressBar(); self.progress.setRange(0,0); self.progress.hide(); main.addWidget(self.progress)
        self.tray=QSystemTrayIcon(self.windowIcon(),self); menu=QMenu()
        show=menu.addAction('Open Optimize Super'); show.triggered.connect(self.show_normal)
        quit_action=menu.addAction('Exit'); quit_action.triggered.connect(self.exit_app)
        self.tray.setContextMenu(menu); self.tray.activated.connect(lambda reason:self.show_normal() if reason==QSystemTrayIcon.DoubleClick else None)
        if QSystemTrayIcon.isSystemTrayAvailable(): self.tray.show()
        self.apply_personalization(); self.navigate(0)
        self.monitor=MonitorThread(self); self.monitor.sample_ready.connect(self.on_sample)
        self.monitor.failed.connect(lambda e:self.store.logger.warning(e)); self.monitor.start()
        self.auto_timer=QTimer(self); self.auto_timer.timeout.connect(self.auto_scan); self.auto_timer.start(60000)
        self.finished_jobs=0
        # Resolve identity once in a background job, never block startup on CIM.
        QTimer.singleShot(100,lambda:self.start_job(lambda p,c:win.machine_info(),self.machine_done,report=False))
    def tr_nav(self,title):
        return VI.get(title,title) if self.store.settings['language']=='Tiếng Việt' else title
    def button(self,text,fn,primary=False,danger=False):
        b=QPushButton(text); b.clicked.connect(fn)
        if primary: b.setObjectName('primary')
        if danger: b.setObjectName('danger')
        return b
    def buttons(self,box,items):
        row=QHBoxLayout()
        for text,fn in items: row.addWidget(self.button(text,fn))
        row.addStretch(); box.addLayout(row)
    def check(self,box,text,checked=False):
        w=QCheckBox(text); w.setChecked(checked); box.addWidget(w); return w
    def notice(self,box,title,detail):
        f,b=card(); b.addWidget(label(title,'eyebrow')); b.addWidget(label(detail,'muted')); box.addWidget(f)
    def navigate(self,index):
        self.stack.setCurrentIndex(index); self.heading.setText(self.tr_nav(NAV[index]))
        for i,b in enumerate(self.nav): b.setChecked(i==index)
        if self.store.settings.get('animations'):
            effect=QGraphicsOpacityEffect(self.stack); self.stack.setGraphicsEffect(effect)
            self.fade=QPropertyAnimation(effect,b'opacity',self); self.fade.setDuration(160)
            self.fade.setStartValue(.35); self.fade.setEndValue(1.0); self.fade.setEasingCurve(QEasingCurve.OutCubic); self.fade.start()
        if index==9: self.refresh_history()
        if index in (3,6): self.refresh_process_tables()
    def show_normal(self): self.showNormal(); self.raise_(); self.activateWindow()
    def confirm(self,title,text):
        return QMessageBox.warning(self,title,text,QMessageBox.Yes|QMessageBox.No,QMessageBox.No)==QMessageBox.Yes
    def error(self,text):
        self.store.logger.error(text); self.status.setText('Operation failed • See report')
        QMessageBox.critical(self,'Operation could not complete',text[-5000:])
    def report(self,result):
        text=result if isinstance(result,str) else json.dumps(result,indent=2,ensure_ascii=False)
        self.show_report(text)
    def show_report(self,text):
        dialog=QDialog(self); dialog.setWindowTitle('Operation report • MTDEV'); dialog.resize(900,600)
        box=QVBoxLayout(dialog); box.addWidget(label('Operation report','title'))
        edit=QPlainTextEdit(); edit.setReadOnly(True); edit.setPlainText(text); box.addWidget(edit)
        row=QHBoxLayout(); save=self.button('Save report…',lambda:self.export_text(text)); row.addWidget(save)
        close=self.button('Close',dialog.accept); row.addWidget(close); box.addLayout(row); dialog.exec()
    def export_text(self,text):
        path,_=QFileDialog.getSaveFileName(self,'Export report','MTDEV-report.txt','Text (*.txt)')
        if path:
            try: Path(path).write_text(text,encoding='utf-8'); self.status.setText('Report exported')
            except OSError as e:self.error(str(e))
    def start_job(self,fn,done=None,report=True,cancellable=False):
        if self.job:
            self.status.setText('Wait for the current operation to finish.'); return
        self.job=Job(fn); self.pending_result=None; self.pending_error=None
        self.job.signals.progress.connect(lambda s:self.status.setText(s[:180]))
        self.job.signals.result.connect(self.job_result)
        self.job.signals.error.connect(self.job_error)
        self.job.signals.finished.connect(self.job_finished)
        self.job_done=done; self.job_report=report
        self.stack.setEnabled(False); self.progress.show(); self.cancel_button.setVisible(cancellable)
        self.status.setText('Working…'); self.pool.start(self.job)
    def job_result(self,result): self.pending_result=result
    def job_error(self,error): self.pending_error=error
    def job_finished(self):
        result,error=self.pending_result,self.pending_error
        callback,report=self.job_done,self.job_report
        self.job=None; self.stack.setEnabled(True); self.progress.hide(); self.cancel_button.hide()
        self.finished_jobs+=1; self.status.setText('Finished • Review the result')
        if error: self.error(error); return
        if report and not self.isVisible() and self.store.settings['notifications'] and self.tray.isVisible():
            self.tray.showMessage('Optimize Super', 'Operation finished. Open the application to review its report.')
        try:
            if callback: callback(result)
            elif report: self.report(result)
        except Exception as e:self.error(str(e))
    def cancel_job(self):
        if self.job: self.job.cancel.set(); self.status.setText('Cancellation requested; finishing the current file safely…')
    def guarded(self,fn):
        try: fn()
        except Exception as e: self.error(str(e))
    def operation(self,description,fn):
        if self.confirm('Confirm system change',description): self.start_job(lambda p,c:fn())
    def dashboard_page(self,box):
        f,b=card(); b.addWidget(label('YOUR SYSTEM. YOUR ADVANTAGE.','eyebrow'))
        b.addWidget(label('Keep performance in view.','title'))
        b.addWidget(label('Live telemetry, careful cleanup and a recovery path for supported settings.','muted'))
        b.addWidget(self.button('SUPER OPTIMIZE  →',lambda:self.navigate(1),primary=True)); box.addWidget(f)
        grid=QGridLayout(); grid.setSpacing(14)
        self.cpu=Metric('CPU LOAD'); self.gpu=Metric('GPU LOAD','#a58bff'); self.ram=Metric('MEMORY'); self.net=Metric('NETWORK','#a58bff')
        for i,w in enumerate((self.cpu,self.gpu,self.ram,self.net)):grid.addWidget(w,i//2,i%2)
        box.addLayout(grid)
        f,b=card(); b.addWidget(label('SYSTEM IDENTITY','eyebrow')); self.identity=label('Reading hardware…','muted'); b.addWidget(self.identity)
        self.uptime=label('Uptime —','muted'); b.addWidget(self.uptime); box.addWidget(f)
        self.disks=Table(['Drive','Used','Capacity','Usage']); self.disks.setMinimumHeight(150); box.addWidget(self.disks)
    def machine_done(self,info):
        self.identity.setText(f"{info['os']} • {info['architecture']}\nCPU  {info['cpu']}\nGPU  {info['gpu']}"+(f"\n{info['hardware_note']}" if 'hardware_note' in info else ''))
    def on_sample(self,s):
        self.snapshot=s
        temp=lambda v: f'{v:.0f} °C' if v is not None else 'Temperature unavailable'
        self.cpu.set(f"{s['cpu']:.0f}%",temp(s['cpu_temp']),s['cpu'])
        self.gpu.set(f"{s['gpu']['usage']:.0f}%" if s['gpu']['usage'] is not None else 'Unavailable',
                     temp(s['gpu']['temp']),s['gpu']['usage'])
        self.gpu.setToolTip(s['gpu']['note'])
        self.ram.set(f"{s['ram_percent']:.0f}%",f"{fmt(s['ram_available'])} available / {fmt(s['ram_total'])}",s['ram_percent'])
        self.net.set(f"↓ {fmt(s['down'])}/s",f"↑ {fmt(s['up'])}/s",(s['down']+s['up'])/1024/1024)
        self.ram_status.setText(f"{fmt(s['ram_used'])} used • {fmt(s['ram_available'])} available • {fmt(s['ram_total'])} total")
        self.gaming_stats.setText(f"CPU {s['cpu']:.0f}%  |  GPU "+(f"{s['gpu']['usage']:.0f}%" if s['gpu']['usage'] is not None else 'unavailable')+'\n'+s['gpu']['note'])
        self.network_live.setText(f"DOWNLOAD  {fmt(s['down'])}/s     UPLOAD  {fmt(s['up'])}/s")
        seconds=int(s['uptime']); days,seconds=divmod(seconds,86400); hours,seconds=divmod(seconds,3600)
        self.uptime.setText(f'Uptime {days}d {hours}h {seconds//60}m  •  {len(s["processes"]):,} visible processes')
        self.disks.populate(s['disks'],['path',lambda r:(r['used'],fmt(r['used'])),lambda r:(r['total'],fmt(r['total'])),lambda r:(r['percent'],f"{r['percent']:.0f}%")])
        if time.monotonic()-self.last_table>2:
            self.refresh_process_tables(); self.last_table=time.monotonic()
        if hasattr(self,'memory_before') and self.memory_before is not None:
            self.ram_change.setText(f'Before: {fmt(self.memory_before)} used  •  Current: {fmt(s["ram_used"])} used. Other applications also affect this value.')
    def optimize_page(self,box):
        self.notice(box,'SELECT YOUR OPERATIONS','Review file locations and sizes before cleanup. Startup and background-process steps are read-only audits. No process is closed automatically.')
        f,b=card(); self.opt_clean=self.check(b,'Clean eligible temporary files (48+ hours old)',True)
        self.opt_recycle=self.check(b,'Empty Recycle Bin — permanent; separate confirmation',self.store.settings.get('opt_recycle',False))
        self.opt_startup=self.check(b,'Identify Windows startup applications',True)
        self.opt_process=self.check(b,'Identify CPU / RAM-heavy background processes',True)
        self.opt_visual=self.check(b,'Reduce Windows client-area animations (backed up first)')
        self.opt_power=self.check(b,'Use supported High performance plan — more heat / battery use',self.store.settings.get('opt_power',False))
        b.addWidget(self.button('SUPER OPTIMIZE',self.prepare_optimize,primary=True)); box.addWidget(f)
        self.opt_report=QPlainTextEdit(); self.opt_report.setReadOnly(True); self.opt_report.setPlaceholderText('Your detailed optimization report will appear here.'); box.addWidget(self.opt_report)
        self.buttons(box,[('Export latest report',lambda:self.export_text(self.opt_report.toPlainText()))])
    def prepare_optimize(self):
        flags={k:w.isChecked() for k,w in [('clean',self.opt_clean),('recycle',self.opt_recycle),('startup',self.opt_startup),('process',self.opt_process),('visual',self.opt_visual),('power',self.opt_power)]}
        if not any(flags.values()):self.error('Select at least one operation.'); return
        def prepare(p,c):
            files=self.cleaner.scan(['User temporary files','Windows temporary files'],p,c) if flags['clean'] else []
            return {'files':files,'notes':list(self.cleaner.notes),'cancelled':c()}
        self.start_job(prepare,lambda r:self.review_optimize(flags,r),report=False,cancellable=True)
    def review_optimize(self,flags,result):
        if result['cancelled']:self.status.setText('Scan cancelled; no changes made.'); return
        files=result['files']
        if flags['clean']:
            dialog=CleanupReview(files,'\n'.join(result['notes']),self)
            if dialog.exec()!=QDialog.Accepted:return
            files=dialog.selected()
        if flags['recycle']:
            try:
                info=recycle_info()
                flags['recycle']=self.confirm('Permanently empty Recycle Bin',f"Location: {info['path']}\n{info['items']} items • {fmt(info['bytes'])}\nThis cannot be undone. Empty it?")
            except Exception as e: self.error(str(e)); return
        changes=[]
        if flags['visual']:changes.append('Save and disable Windows client-area UI animations using the Windows API.')
        if flags['power']:changes.append('Save and activate High performance if supported; increases power use and heat.')
        if changes and not self.confirm('Confirm selected performance settings','\n'.join(changes)+'\nBackups appear in Restore Center.'):return
        def execute(p,c):
            reports=[]
            def step(name,fn):
                p(name)
                try:reports.append(name+'\n'+json.dumps(fn(),indent=2,ensure_ascii=False))
                except Exception as e:reports.append(name+'\nFAILED: '+str(e))
            if flags['clean']:step('Temporary-file cleanup',lambda:self.cleaner.delete(files,self.store,p,c))
            if flags['recycle']:step('Recycle Bin',lambda:empty_recycle(self.store))
            if flags['startup']:step('Startup audit (no entries disabled)',self.startup.list)
            if flags['process']:
                step('Resource audit (no processes closed)',lambda:{'top_cpu':sorted(self.snapshot.get('processes',[]),key=lambda r:r['cpu'],reverse=True)[:10], 'top_ram':sorted(self.snapshot.get('processes',[]),key=lambda r:r['ram'],reverse=True)[:10]})
            if flags['visual']:step('Visual effects preference',self.engine.animation_setting)
            if flags['power']:step('Power plan',self.engine.power)
            text='OPTIMIZE SUPER | MTDEV\n\n'+'\n\n'.join(reports)
            self.store.record('optimization_report',after={'report':text},status='completed',detail='See individual operations for success/failure. No synthetic performance score.')
            return text
        self.start_job(execute,self.optimize_done)
    def optimize_done(self,text):self.opt_report.setPlainText(text); self.report(text)
    def gaming_page(self,box):
        self.notice(box,'GAMING, WITHOUT THE GUESSWORK','Game Mode and GPU scheduling are managed by Windows. HAGS requires compatible hardware and a WDDM driver; the Windows graphics page is the authoritative availability check. No FPS estimate is generated.')
        self.gaming_stats=label('Waiting for CPU / GPU readings…','value'); box.addWidget(self.gaming_stats)
        self.buttons(box,[('Windows Game Mode',lambda:self.open_tool('Game Mode')),('GPU scheduling availability',lambda:self.open_tool('GPU scheduling'))])
        box.addWidget(self.button('Read GPU scheduling diagnostics',lambda:self.start_job(lambda p,c:__import__('modules.gaming',fromlist=['scheduling_check']).scheduling_check(self.store,p,c),cancellable=True)))
        self.buttons(box,[('Enable Game Mode preference',lambda:self.operation('Back up and enable the current user Game Mode preference? Windows may need sign-out.',self.engine.game_mode)),('Review background apps',lambda:self.navigate(6))])
        self.games=Table(['Game','Executable','Power profile']); box.addWidget(self.games); self.refresh_games()
        row=QHBoxLayout(); self.game_profile=QComboBox(); self.game_profile.addItems(['Keep current','Balanced','High performance']); row.addWidget(self.game_profile)
        row.addWidget(self.button('Save profile for selected game',lambda:self.guarded(self.save_game_profile))); box.addLayout(row)
        self.buttons(box,[('Add game…',self.add_game),('Launch selected game',lambda:self.guarded(self.launch_game)),('Remove game',lambda:self.guarded(self.remove_game))])
        self.buttons(box,[('Restore last power change',lambda:self.restore_latest('power')),('Windows Power Options',lambda:self.open_tool('Power Options'))])
        self.notice(box,'PROFILE BEHAVIOR','A game profile optionally changes the Windows power plan after confirmation. Restore the original plan after playing using the button above. This app does not inject into games or disable services.')
    def refresh_games(self):self.games.populate(self.store.settings['games'],['name','path','profile'])
    def add_game(self):
        path,_=QFileDialog.getOpenFileName(self,'Add game executable','','Windows executable (*.exe)')
        if not path:return
        if any(g['path'].casefold()==path.casefold() for g in self.store.settings['games']):return
        self.store.settings['games'].append({'name':Path(path).stem,'path':path,'profile':'Keep current'}); self.store.save(); self.refresh_games()
    def save_game_profile(self):
        selected=self.games.selected()
        for g in self.store.settings['games']:
            if g['path']==selected['path']:g['profile']=self.game_profile.currentText()
        self.store.save(); self.refresh_games()
    def remove_game(self):
        row=self.games.selected(); self.store.settings['games']=[g for g in self.store.settings['games'] if g['path']!=row['path']]; self.store.save(); self.refresh_games()
    def launch_game(self):
        win.require_windows(); game=self.games.selected(); path=Path(game['path'])
        if not path.is_file() or path.suffix.lower()!='.exe':raise ValueError('The saved game executable is unavailable.')
        text=f"Launch {game['name']}?\n{path}"
        if game['profile']!='Keep current':text+=f"\nApply {game['profile']} power plan, backed up first. Restore it after playing. High performance can increase heat and battery use."
        if not self.confirm('Launch game',text):return
        def work(p,c):
            if game['profile']!='Keep current':self.engine.power(game['profile']=='Balanced')
            subprocess.Popen([str(path)],cwd=str(path.parent)); return 'Game launched. Use Restore last power change when finished if a power profile was applied.'
        self.start_job(work)
    def ram_page(self,box):
        self.notice(box,'REAL MEMORY MANAGEMENT','Windows manages memory caches. Safely review memory use and close a selected user application after saving your work. Closing a process is irreversible. No cache purges or working-set tricks are used.')
        self.ram_status=label('Waiting for memory data…','value'); box.addWidget(self.ram_status)
        self.ram_change=label('Select a non-essential application to measure before / after usage.','muted'); box.addWidget(self.ram_change); self.memory_before=None
        self.ram_table=Table(['Application','PID','RAM','CPU']); self.ram_table.sortItems(2,Qt.DescendingOrder); box.addWidget(self.ram_table)
        box.addWidget(self.button('Close selected application…',lambda:self.close_process(self.ram_table),danger=True))
    def close_process(self,table):
        def work():
            row=table.selected()
            if not self.confirm('Close application',f"Close {row['name']} (PID {row['pid']})?\nUnsaved work may be lost. Protected, Windows, service and other-user processes are blocked. This cannot be undone."):return
            self.memory_before=self.snapshot.get('ram_used')
            self.start_job(lambda p,c:Processes().terminate(row,self.store))
        self.guarded(work)
    def cleaner_page(self,box):
        self.notice(box,'SCAN FIRST. REVIEW. THEN CLEAN.','Estimated savings exclude recent files, executable files and redirected paths. Locked or changed files are skipped. Large-file and duplicate scans are read-only and never delete personal files.')
        f,b=card(); self.categories={}
        for name in self.cleaner.roots:self.categories[name]=self.check(b,name,name=='User temporary files')
        b.addWidget(self.button('Scan selected cleanup locations',self.scan_cleanup,primary=True)); box.addWidget(f)
        self.buttons(box,[('Review / empty Recycle Bin',self.recycle_dialog),('Scan large files (100 MB+)…',lambda:self.scan_analysis(False)),('Scan duplicates (SHA-256)…',lambda:self.scan_analysis(True))])
        self.analysis=Table(['Full location','Size','SHA-256 duplicate group']); box.addWidget(self.analysis)
        self.analysis_summary=label('Choose a folder to analyze. Duplicate files require manual review.','muted'); box.addWidget(self.analysis_summary)
        self.buttons(box,[('Open selected file location',lambda:self.guarded(self.reveal_analysis))])
    def scan_cleanup(self):
        categories=[name for name,w in self.categories.items() if w.isChecked()]
        if not categories:self.error('Select at least one cleanup category.');return
        self.start_job(lambda p,c:{'files':self.cleaner.scan(categories,p,c),'notes':list(self.cleaner.notes),'cancelled':c()},self.review_cleanup,report=False,cancellable=True)
    def review_cleanup(self,result):
        if result['cancelled']:self.status.setText('Scan cancelled; no files deleted.');return
        dialog=CleanupReview(result['files'],'\n'.join(result['notes']),self)
        if dialog.exec()==QDialog.Accepted:
            chosen=dialog.selected()
            if chosen:self.start_job(lambda p,c:self.cleaner.delete(chosen,self.store,p,c),cancellable=True)
    def recycle_dialog(self):
        def work():
            info=recycle_info()
            if self.confirm('Permanently empty Recycle Bin',f"{info['path']}\n{info['items']} items • {fmt(info['bytes'])}\nFiles cannot be recovered by this app. Continue?"):
                self.start_job(lambda p,c:empty_recycle(self.store))
        self.guarded(work)
    def scan_analysis(self,duplicate):
        root=QFileDialog.getExistingDirectory(self,'Choose a folder for read-only analysis')
        if root:self.start_job(lambda p,c:analyze(root,duplicate,p,c),self.analysis_done,report=False,cancellable=True)
    def analysis_done(self,result):
        rows=result['rows']; self.analysis.populate(rows,['path',lambda r:(r['size'],fmt(r['size'])),'group'])
        errors=result['errors']; self.analysis_summary.setText(f"{'Cancelled • partial results' if result['cancelled'] else 'Scan complete'} • {len(rows):,} matches • {len(errors)} inaccessible paths. No files deleted.")
        if errors:self.report({'scan_warnings':errors})
    def reveal_analysis(self):
        win.require_windows(); row=self.analysis.selected(); path=Path(row['path'])
        if not path.exists():raise FileNotFoundError('This file no longer exists.')
        subprocess.Popen([win.system_exe('explorer.exe'),'/select,',str(path)])
    def startup_page(self,box):
        self.notice(box,'STARTUP CONTROL','Lists 64/32-bit Run keys and the user / shared Startup folders. Publisher uses executable CompanyName metadata when present (not signature verification). Scheduled tasks, packaged startup apps and services are managed through Windows Settings.')
        self.startup_table=Table(['Application','Publisher metadata','Startup location','Command']); box.addWidget(self.startup_table)
        self.buttons(box,[('Refresh startup entries',self.refresh_startup),('Disable selected…',lambda:self.guarded(self.disable_startup)),('Enable / restore previous entry',lambda:self.navigate(9))])
        box.addWidget(self.button('Open Windows startup settings',lambda:self.guarded(lambda:self.open_uri('ms-settings:startupapps'))))
    def refresh_startup(self):
        self.start_job(lambda p,c:self.startup.list(),lambda rows:self.startup_table.populate(rows,['name','publisher','location','command']),report=False)
    def disable_startup(self):
        row=self.startup_table.selected()
        if self.confirm('Disable startup application',f"Disable {row['name']}?\n{row['location']}\nDo not disable an entry you do not recognize. Its original configuration will be saved in Restore Center."):
            self.start_job(lambda p,c:self.startup.disable(row))
    def process_page(self,box):
        self.notice(box,'BACKGROUND PROCESS REVIEW','CPU values are sampled per process; multicore applications may exceed 100%. Click headers to sort. Windows processes, services, security processes and applications owned by other users cannot be terminated.')
        self.search=QLineEdit(); self.search.setPlaceholderText('Search application name or PID…'); self.search.textChanged.connect(self.refresh_process_tables); box.addWidget(self.search)
        self.process_table=Table(['Application','PID','CPU','RAM','User']); self.process_table.sortItems(2,Qt.DescendingOrder); box.addWidget(self.process_table)
        self.buttons(box,[('Close selected process…',lambda:self.close_process(self.process_table))])
    def refresh_process_tables(self,*_):
        if not self.snapshot:return
        rows=self.snapshot['processes']
        if self.stack.currentIndex()==3:
            self.ram_table.populate(sorted(rows,key=lambda r:r['ram'],reverse=True),['name','pid',lambda r:(r['ram'],fmt(r['ram'])),lambda r:(r['cpu'],f"{r['cpu']:.1f}%")])
        if self.stack.currentIndex()==6:
            query=self.search.text().lower(); filtered=[r for r in rows if query in r['name'].lower() or query in str(r['pid'])]
            self.process_table.populate(filtered,['name','pid',lambda r:(r['cpu'],f"{r['cpu']:.1f}%"),lambda r:(r['ram'],fmt(r['ram'])),'user'])
    def network_page(self,box):
        self.notice(box,'CONNECTION & DNS','DNS changes affect name resolution and do not guarantee lower ping. Only the selected physical adapter IPv4 DNS is changed. Static/DHCP provenance is backed up; IPv6 is preserved. Administrator permission is required to change or restore DNS.')
        self.network_live=label('Waiting for network counters…','value'); box.addWidget(self.network_live)
        self.network_table=Table(['Interface','Connected','Link Mbps','Addresses']); box.addWidget(self.network_table)
        row=QHBoxLayout(); self.adapter=QComboBox(); self.adapter.setMinimumWidth(230); row.addWidget(self.adapter,1)
        self.dns_profile=QComboBox(); self.dns_profile.addItems(PROFILES); row.addWidget(self.dns_profile); box.addLayout(row)
        self.buttons(box,[('Refresh connections / adapters',self.refresh_network),('Apply DNS profile…',lambda:self.guarded(self.apply_dns)),('Flush resolver cache',lambda:self.operation('Flush the Windows DNS resolver cache? No settings are changed.',self.network.flush))])
        box.addWidget(self.button('Restore last DNS change',lambda:self.restore_latest('dns')))
    def refresh_network(self):
        def work(p,c):return {'info':self.network.info(),'adapters':self.network.adapters() if win.IS_WINDOWS else []}
        def done(r):
            self.network_table.populate(r['info'],['name',lambda a:'Yes' if a['up'] else 'No','speed_mbps',lambda a:', '.join(a['addresses'])])
            self.adapter.clear()
            for a in r['adapters']:self.adapter.addItem(f"{a['Name']} ({a['Status']})",a)
        self.start_job(work,done,report=False)
    def apply_dns(self):
        adapter=self.adapter.currentData()
        if not adapter:raise ValueError('Refresh adapters and choose a physical adapter first.')
        profile=self.dns_profile.currentText()
        self.operation(f"Set {adapter['Name']} IPv4 DNS to {profile} ({', '.join(PROFILES[profile])})?\nCurrent configuration is saved first. This can affect connectivity and organizational name resolution.",lambda:self.network.apply(adapter,profile))
    def tools_page(self,box):
        self.notice(box,'NATIVE WINDOWS CONTROLS','Open official Windows tools. These shortcuts do not change settings by themselves. Windows may request administrator permission for subsequent actions.')
        grid=QGridLayout()
        for i,name in enumerate(list(win.TOOLS)[:9]):grid.addWidget(self.button('↗  '+name,lambda checked=False,n=name:self.open_tool(n)),i//2,i%2)
        box.addLayout(grid)
    def open_uri(self,uri):win.require_windows();os.startfile(uri)
    def open_tool(self,name):self.guarded(lambda:self.status.setText(win.open_tool(name)))
    def restore_page(self,box):
        self.notice(box,'A RECORD BEFORE EVERY CHANGE','Undo saved settings in reverse order. External changes are detected and protected. Failed or interrupted operations retain their original snapshots. Deleted files and closed processes cannot be restored by this app.')
        self.history_table=Table(['Time (UTC)','Operation','Status','Restored','Details']); box.addWidget(self.history_table)
        self.buttons(box,[('Refresh history',self.refresh_history),('View saved details',lambda:self.guarded(lambda:self.report(self.history_table.selected()))),('Undo selected change…',lambda:self.guarded(self.undo_selected))])
        self.buttons(box,[('Create Windows restore point…',lambda:self.operation('Create a Windows System Protection restore point? Requires administrator rights and enabled System Protection. Windows may limit checkpoint frequency.',self.engine.restore_point)),('Restore Default Settings…',self.restore_all)])
        self.buttons(box,[('Open Windows System Restore',lambda:self.open_tool('System Restore')),('Export audit history…',lambda:self.guarded(lambda:self.export_text(json.dumps(self.store.history(),indent=2,ensure_ascii=False))))])
        self.notice(box,'WHAT “RESTORE DEFAULT SETTINGS” MEANS','Restore the original values saved before this app’s changes, newest first. It does not reset unrelated Windows settings. Use Windows System Restore for a broader restore point recovery.')
    def refresh_history(self):
        self.guarded(lambda:self.history_table.populate(self.store.history(),['time','kind','status',lambda r:'Yes' if r.get('undone') else 'No','detail']))
    def undo_selected(self):
        entry=self.history_table.selected()
        if self.confirm('Restore original setting',f"Undo {entry['kind']} from {entry['time']}?\nOnly the saved original setting is restored. Restore newer changes to the same setting first."):
            self.start_job(lambda p,c:self.engine.undo(entry))
    def restore_latest(self,kind):
        def work():
            item=next((x for x in self.store.history() if x['kind']==kind and not x.get('undone')),None)
            if not item:raise ValueError('No saved change of this type is available.')
            self.operation(f"Restore the original {kind} setting saved at {item['time']}?",lambda:self.engine.undo(item))
        self.guarded(work)
    def restore_all(self):
        self.operation('Restore all supported changes made by this app, newest first? External changes will be protected. Cleanup and closed processes are irreversible.',self.engine.restore_defaults)
    def settings_page(self,box):
        f,b=card(); b.addWidget(label('PERSONALIZE','eyebrow'))
        self.theme=QComboBox();self.theme.addItems(['Dark','Light']);self.theme.setCurrentText(self.store.settings['theme']);b.addWidget(label('Appearance'));b.addWidget(self.theme)
        self.language=QComboBox();self.language.addItems(['English','Tiếng Việt']);self.language.setCurrentText(self.store.settings['language']);b.addWidget(label('Navigation language / Ngôn ngữ điều hướng'));b.addWidget(self.language)
        b.addWidget(label('Technical operation descriptions and reports remain in English.','muted'))
        self.animations=self.check(b,'Animate page transitions',self.store.settings['animations'])
        self.min_tray=self.check(b,'Minimize to system tray on close',self.store.settings['tray'])
        self.notifications=self.check(b,'Show desktop notifications',self.store.settings['notifications'])
        self.pref_power=self.check(b,'Select power-plan change by default in Super Optimize',self.store.settings['opt_power'])
        self.pref_recycle=self.check(b,'Select Recycle Bin by default (confirmation still required)',self.store.settings['opt_recycle'])
        b.addWidget(self.button('Save preferences',self.save_preferences,primary=True));box.addWidget(f)
        f,b=card();b.addWidget(label('AUTOMATIC CLEANUP REVIEW','eyebrow'))
        self.auto=self.check(b,'Periodically scan user temporary files while this app is running',self.store.settings['auto_cleanup'])
        self.hours=QSpinBox();self.hours.setRange(1,720);self.hours.setSuffix(' hours');self.hours.setValue(self.store.settings['cleanup_hours']);b.addWidget(self.hours)
        b.addWidget(label('Automatic scans notify you to review locations and sizes. Deletion always needs your confirmation. No scheduled task is installed.','muted'))
        b.addWidget(self.button('Save automatic cleanup configuration',self.save_preferences));box.addWidget(f)
        self.buttons(box,[('Enable app startup…',lambda:self.operation('Back up the current startup entry and launch this app when this Windows account signs in?',lambda:self.engine.self_startup(True))),('Disable app startup…',lambda:self.operation('Back up and remove this app’s startup entry?',lambda:self.engine.self_startup(False)))])
        self.buttons(box,[('Restart as administrator…',self.request_elevation),('Open logs / backups folder',lambda:self.guarded(self.open_data)),('Reset app preferences…',self.reset_preferences)])
        self.notice(box,'OFFLINE BY DESIGN','Core tools do not require internet access. No telemetry or fabricated scores. Backups and logs remain on this PC. MTDEV does not disable security, firewall, updates or essential services.')
    def save_preferences(self):
        self.store.settings.update(theme=self.theme.currentText(),language=self.language.currentText(),
            animations=self.animations.isChecked(),tray=self.min_tray.isChecked(),notifications=self.notifications.isChecked(),
            auto_cleanup=self.auto.isChecked(),cleanup_hours=self.hours.value(),opt_power=self.pref_power.isChecked(),opt_recycle=self.pref_recycle.isChecked())
        self.store.save();self.apply_personalization();self.status.setText('Preferences saved')
        self.opt_power.setChecked(self.store.settings['opt_power']);self.opt_recycle.setChecked(self.store.settings['opt_recycle'])
    def apply_personalization(self):
        self.setStyleSheet(stylesheet(self.store.settings['theme']))
        self.sidebar.setFixedWidth(250 if self.store.settings['language']=='Tiếng Việt' else 211)
        for i,title in enumerate(NAV):self.nav[i].setText(f'{i+1:02}   {self.tr_nav(title)}')
        self.heading.setText(self.tr_nav(NAV[self.stack.currentIndex()]))
    def reset_preferences(self):
        if not self.confirm('Reset app preferences','Reset application preferences? Game profiles are retained. Windows settings and backups are not reset; use Restore Center for those.'):return
        games=self.store.settings['games'];self.store.settings=deepcopy(DEFAULTS);self.store.settings['games']=games;self.store.save()
        self.theme.setCurrentText('Dark');self.language.setCurrentText('English');self.animations.setChecked(True)
        self.min_tray.setChecked(False);self.notifications.setChecked(True);self.auto.setChecked(False);self.hours.setValue(24)
        self.pref_power.setChecked(False);self.pref_recycle.setChecked(False);self.opt_power.setChecked(False);self.opt_recycle.setChecked(False);self.apply_personalization()
    def open_data(self):win.require_windows();os.startfile(str(self.store.root))
    def request_elevation(self):
        def work():
            if win.admin():self.status.setText('Already running as administrator.');return
            if self.confirm('Windows administrator permission','Restart this application with administrator rights? Windows will show a UAC prompt. Use the same account so your backups stay associated with it.'):
                win.elevate();self.exit_requested=True;self.close()
        self.guarded(work)
    def auto_scan(self):
        settings=self.store.settings
        if not settings['auto_cleanup'] or self.job:return
        if time.monotonic()-self.last_cleanup < settings['cleanup_hours']*3600:return
        self.last_cleanup=time.monotonic()
        def done(result):
            if not result['files']:self.status.setText('Automatic scan finished • no eligible files');return
            self.show_normal()
            if settings['notifications'] and self.tray.isVisible():self.tray.showMessage('Optimize Super • Review cleanup',f"{len(result['files'])} eligible files found. Review before deleting.")
            self.review_cleanup(result)
        self.start_job(lambda p,c:{'files':self.cleaner.scan(['User temporary files'],p,c),'notes':list(self.cleaner.notes),'cancelled':c()},done,report=False,cancellable=True)
    def exit_app(self):self.exit_requested=True;self.close()
    def closeEvent(self,event):
        if self.job:
            event.ignore();self.status.setText('An operation is still running. Cancel scans or wait for completion before exiting.');return
        if self.store.settings['tray'] and not self.exit_requested and self.tray.isVisible():
            self.hide();event.ignore();return
        self.monitor.requestInterruption();self.monitor.wait(6000)
        if self.monitor.isRunning():event.ignore();self.status.setText('Waiting for the monitoring thread to stop…');QTimer.singleShot(1000,self.close);return
        self.tray.hide();event.accept()
