"""Optional executable CompanyName metadata; not a claim of signature verification."""
import ctypes
from pathlib import Path
import re
from core import windows as win

def publisher(command):
    if not win.IS_WINDOWS:return 'Unavailable'
    try:
        text=str(command).strip()
        if text.startswith('"'):path=text.split('"',2)[1]
        else:
            match=re.match(r'(.+?\.exe)(?:\s|$)',text,re.I)
            if not match:return 'Unavailable'
            path=match.group(1)
        import os
        path=os.path.expandvars(path)
        if not Path(path).is_file():return 'Unavailable'
        lib=ctypes.WinDLL('version',use_last_error=True)
        lib.GetFileVersionInfoSizeW.argtypes=[ctypes.c_wchar_p,ctypes.c_void_p]
        lib.GetFileVersionInfoSizeW.restype=ctypes.c_ulong
        size=lib.GetFileVersionInfoSizeW(path,None)
        if not size:return 'Unavailable'
        buffer=ctypes.create_string_buffer(size)
        lib.GetFileVersionInfoW.argtypes=[ctypes.c_wchar_p,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_void_p]
        if not lib.GetFileVersionInfoW(path,0,size,buffer):return 'Unavailable'
        query=lib.VerQueryValueW;query.argtypes=[ctypes.c_void_p,ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_uint)]
        pointer=ctypes.c_void_p();length=ctypes.c_uint()
        translations=[]
        if query(buffer,r'\VarFileInfo\Translation',ctypes.byref(pointer),ctypes.byref(length)):
            words=ctypes.cast(pointer,ctypes.POINTER(ctypes.c_ushort))
            translations=[(words[i],words[i+1]) for i in range(0,length.value//2-1,2)]
        for lang,codepage in translations:
            key=f'\\StringFileInfo\\{lang:04x}{codepage:04x}\\CompanyName'
            if query(buffer,key,ctypes.byref(pointer),ctypes.byref(length)) and length.value>1:
                return ctypes.wstring_at(pointer,length.value-1).strip() or 'Unavailable'
    except (OSError,ValueError,TypeError,AttributeError):pass
    return 'Unavailable'
