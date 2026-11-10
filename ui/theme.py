DARK = {'bg':'#080c19','panel':'#111a30','card':'#142039','text':'#ecf2ff','muted':'#94a5c5','line':'#263653','input':'#0c1427','blue':'#51d4ff','purple':'#a58bff'}
LIGHT = {'bg':'#edf2fa','panel':'#ffffff','card':'#f7f9ff','text':'#172744','muted':'#526783','line':'#d4deed','input':'#ffffff','blue':'#0076b3','purple':'#6e46cc'}

def stylesheet(mode):
    c = DARK if mode=='Dark' else LIGHT
    return f'''
    QWidget {{ color:{c['text']}; font-family:"Segoe UI","Inter",sans-serif; font-size:13px; }}
    QMainWindow, QDialog {{ background:{c['bg']}; }}
    QWidget#shell, QScrollArea, QScrollArea > QWidget > QWidget {{ background:{c['bg']}; }}
    QFrame#sidebar {{ background:{c['panel']}; border-right:1px solid {c['line']}; }}
    QFrame#card {{ background:{c['card']}; border:1px solid {c['line']}; border-radius:16px; }}
    QLabel {{ background:transparent; }}
    QLabel#title {{ font-size:29px; font-weight:700; }}
    QLabel#eyebrow {{ font-size:11px; color:{c['blue']}; font-weight:700; letter-spacing:2px; }}
    QLabel#muted {{ color:{c['muted']}; }}
    QLabel#brand {{ font-size:25px; font-weight:800; letter-spacing:2px; }}
    QLabel#value {{ font-size:24px; font-weight:650; }}
    QPushButton {{ background:{c['card']}; border:1px solid {c['line']}; border-radius:9px; padding:10px 15px; font-weight:600; }}
    QPushButton:hover {{ border-color:{c['blue']}; background:{c['panel']}; }}
    QPushButton:pressed {{ background:{c['line']}; }}
    QPushButton:disabled {{ color:{c['muted']}; }}
    QPushButton#primary {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2069d7,stop:1 #754be0); color:white; border:0; padding:15px 24px; font-size:15px; }}
    QPushButton#nav {{ text-align:left; padding:11px 14px; border:0; background:transparent; color:{c['muted']}; }}
    QPushButton#nav:checked {{ color:{c['blue']}; background:{c['card']}; border-left:3px solid {c['blue']}; }}
    QPushButton#danger {{ color:#f47d94; }}
    QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit {{ background:{c['input']}; border:1px solid {c['line']}; border-radius:8px; padding:8px; selection-background-color:#395dae; }}
    QComboBox QAbstractItemView {{ background:{c['panel']}; selection-background-color:#395dae; }}
    QCheckBox {{ spacing:9px; padding:5px; }}
    QCheckBox::indicator {{ width:17px; height:17px; border-radius:4px; border:1px solid {c['muted']}; background:{c['input']}; }}
    QCheckBox::indicator:checked {{ background:#526ce3; border:1px solid #51d4ff; }}
    QTableWidget {{ background:{c['panel']}; alternate-background-color:{c['card']}; border:1px solid {c['line']}; border-radius:10px; gridline-color:{c['line']}; selection-background-color:#304b77; selection-color:white; }}
    QTableWidget::item {{ padding:6px; }}
    QHeaderView::section {{ background:{c['card']}; color:{c['muted']}; padding:10px; border:0; border-bottom:1px solid {c['line']}; font-size:11px; font-weight:600; }}
    QProgressBar {{ border:0; border-radius:4px; background:{c['line']}; height:7px; text-align:center; }}
    QProgressBar::chunk {{ border-radius:4px; background:#5686f5; }}
    QScrollBar:vertical {{ background:transparent; width:8px; }}
    QScrollBar::handle:vertical {{ background:{c['line']}; border-radius:4px; min-height:30px; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
    QToolTip {{ background:{c['panel']}; color:{c['text']}; border:1px solid {c['line']}; padding:5px; }}
    '''
