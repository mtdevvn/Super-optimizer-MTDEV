"""Atomic, per-user settings and append-only-operation journal snapshots."""
from __future__ import annotations
import json
from copy import deepcopy
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import threading
import uuid
from datetime import datetime, timezone

DEFAULTS = {'theme': 'Dark', 'language': 'English', 'animations': True,
            'tray': False, 'notifications': True, 'auto_cleanup': False,
            'cleanup_hours': 24, 'cleanup_categories': ['User temporary files'],
            'opt_power': False, 'opt_recycle': False, 'games': []}

def data_root():
    return Path(os.environ.get('LOCALAPPDATA', str(Path.home() / '.local/share'))) / 'MTDEV' / 'OptimizeSuper'

def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with tmp.open('w', encoding='utf-8') as f:
            json.dump(value, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)

class Store:
    def __init__(self, root=None):
        self.root = Path(root) if root else data_root()
        self.lock = threading.RLock()
        for name in ('logs', 'backups', 'data', 'config'):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self.settings_path = self.root / 'config/settings.json'
        self.settings = deepcopy(DEFAULTS) | self.read(self.settings_path, {})
        handler = RotatingFileHandler(self.root / 'logs/app.log', maxBytes=2_000_000, backupCount=3, encoding='utf-8')
        self.logger = logging.getLogger('mtdev.' + uuid.uuid4().hex)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    @staticmethod
    def read(path, default):
        if not path.exists():
            return default
        # Corrupt state must never silently reset backups or safety settings.
        with path.open(encoding='utf-8') as f:
            return json.load(f)
    def save(self):
        with self.lock:
            atomic_json(self.settings_path, self.settings)
    def record(self, kind, before=None, after=None, status='prepared', detail=''):
        with self.lock:
            item = {'id': uuid.uuid4().hex, 'time': datetime.now(timezone.utc).isoformat(),
                    'kind': kind, 'before': before, 'after': after,
                    'status': status, 'detail': detail, 'undone': False}
            atomic_json(self.root / 'backups' / (item['id'] + '.json'), item)
            self.logger.info('%s %s %s', kind, status, detail)
            return item
    def update(self, item, **values):
        with self.lock:
            item.update(values)
            atomic_json(self.root / 'backups' / (item['id'] + '.json'), item)
            self.logger.info('%s %s %s', item['kind'], item['status'], item.get('detail',''))
    def history(self):
        return sorted([self.read(p, {}) for p in (self.root / 'backups').glob('*.json')],
                      key=lambda x: x['time'], reverse=True)
