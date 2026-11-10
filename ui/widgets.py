from collections import deque
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QPainterPath
from PySide6.QtWidgets import (QFrame,QVBoxLayout,QHBoxLayout,QLabel,QTableWidget,
 QTableWidgetItem,QHeaderView,QAbstractItemView,QDialog,QDialogButtonBox,QPushButton)

def fmt(value):
    number=float(value)
    for unit in ('B','KB','MB','GB','TB'):
        if abs(number)<1024 or unit=='TB': return f'{number:,.1f} {unit}'
        number/=1024

def label(text,kind=None):
    w=QLabel(text); w.setWordWrap(True)
    if kind: w.setObjectName(kind)
    return w

def card():
    frame=QFrame(); frame.setObjectName('card')
    layout=QVBoxLayout(frame); layout.setContentsMargins(20,18,20,18); layout.setSpacing(10)
    return frame,layout

class Sparkline(QFrame):
    def __init__(self,color='#51d4ff'):
        super().__init__(); self.values=deque(maxlen=50); self.color=color; self.setFixedHeight(46)
    def add(self,value):
        self.values.append(value); self.update()
    def paintEvent(self,event):
        if len(self.values)<2: return
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        path=QPainterPath(); vals=list(self.values); peak=max(100,max(vals))
        for i,v in enumerate(vals):
            x=i*self.width()/(len(vals)-1); y=self.height()-4-v/peak*(self.height()-8)
            path.moveTo(x,y) if i==0 else path.lineTo(x,y)
        p.setPen(QPen(QColor(self.color),2)); p.drawPath(path)

class Metric(QFrame):
    def __init__(self,name,color='#51d4ff'):
        super().__init__(); self.setObjectName('card')
        box=QVBoxLayout(self); box.setContentsMargins(20,16,20,14)
        self.heading=label(name,'eyebrow'); box.addWidget(self.heading)
        self.value=label('—','value'); box.addWidget(self.value)
        self.detail=label('Waiting for a real sample','muted'); box.addWidget(self.detail)
        self.graph=Sparkline(color); box.addWidget(self.graph)
    def set(self,value,detail,graph=None):
        self.value.setText(value); self.detail.setText(detail)
        if graph is not None: self.graph.add(graph)

class SortItem(QTableWidgetItem):
    def __init__(self,value,display=None):
        super().__init__(str(value) if display is None else str(display)); self.value=value
    def __lt__(self,other):
        return self.value<other.value if isinstance(other,SortItem) and type(self.value)==type(other.value) else super().__lt__(other)

class Table(QTableWidget):
    def __init__(self,headers):
        super().__init__(0,len(headers)); self.setHorizontalHeaderLabels(headers)
        self.setAlternatingRowColors(True); self.setShowGrid(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows); self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers); self.verticalHeader().hide()
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.horizontalHeader().setStretchLastSection(True); self.setMinimumHeight(230)
        self.setSortingEnabled(True)
    def populate(self,rows,columns):
        selected=self.currentRow(); selected_data=self.item(selected,0).data(Qt.UserRole) if selected>=0 and self.item(selected,0) else None
        sort_col=self.horizontalHeader().sortIndicatorSection(); order=self.horizontalHeader().sortIndicatorOrder()
        self.setSortingEnabled(False); self.setRowCount(len(rows))
        for i,row in enumerate(rows):
            for j,col in enumerate(columns):
                val=col(row) if callable(col) else row.get(col,'')
                cell=SortItem(val[0],val[1]) if isinstance(val,tuple) else SortItem(val)
                cell.setToolTip(cell.text()); cell.setData(Qt.UserRole,row)
                self.setItem(i,j,cell)
        self.setSortingEnabled(True); self.sortItems(sort_col,order)
        if selected_data:
            for i in range(self.rowCount()):
                current=self.item(i,0).data(Qt.UserRole)
                key=lambda d:(d.get('pid'),d.get('created')) if 'pid' in d else (d.get('id'),d.get('path'),d.get('name'))
                if key(current)==key(selected_data): self.selectRow(i); break
    def selected(self):
        item=self.item(self.currentRow(),0)
        if not item: raise ValueError('Select a row first.')
        return item.data(Qt.UserRole)

class CleanupReview(QDialog):
    def __init__(self,candidates,notes='',parent=None):
        super().__init__(parent); self.setWindowTitle('Review cleanup • OPTIMIZE SUPER | MTDEV'); self.resize(1020,650)
        self.candidates=candidates
        box=QVBoxLayout(self)
        box.addWidget(label(f'{len(candidates):,} eligible files • {fmt(sum(c.size for c in candidates))} estimated','title'))
        box.addWidget(label('Only checked files will be permanently deleted. Files newer than 48 hours, executables, links and changed files are excluded. Cleanup cannot be undone.','muted'))
        self.table=QTableWidget(len(candidates),4)
        self.table.setHorizontalHeaderLabels(['Delete','Full location','Size','Category'])
        self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        for i,c in enumerate(candidates):
            check=QTableWidgetItem(); check.setFlags(Qt.ItemIsEnabled|Qt.ItemIsUserCheckable); check.setCheckState(Qt.Checked)
            self.table.setItem(i,0,check)
            for j,val in enumerate((c.path,fmt(c.size),c.category),1):
                item=QTableWidgetItem(val); item.setToolTip(val); self.table.setItem(i,j,item)
        box.addWidget(self.table)
        if notes: box.addWidget(label(notes[:1500],'muted'))
        row=QHBoxLayout()
        for title,state in [('Select all',Qt.Checked),('Select none',Qt.Unchecked)]:
            b=QPushButton(title); b.clicked.connect(lambda checked=False,s=state:self.check_all(s)); row.addWidget(b)
        box.addLayout(row)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText('Confirm selected files')
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); box.addWidget(buttons)
    def check_all(self,state):
        for i in range(self.table.rowCount()): self.table.item(i,0).setCheckState(state)
    def selected(self):
        return [c for i,c in enumerate(self.candidates) if self.table.item(i,0).checkState()==Qt.Checked]
