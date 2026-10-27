"""Windows per-pixel-alpha compositor for a Tk toplevel.

Uses UpdateLayeredWindow with premultiplied BGRA, preserving soft edges.
https://learn.microsoft.com/windows/win32/api/winuser/nf-winuser-updatelayeredwindow
"""
import ctypes as C
from ctypes import wintypes as W
from PIL import ImageDraw, ImageFont
from orb_art import artwork


class BitmapHeader(C.Structure):
    _fields_=[('size',W.DWORD),('width',W.LONG),('height',W.LONG),
              ('planes',W.WORD),('bits',W.WORD),('compression',W.DWORD),
              ('image_size',W.DWORD),('xppm',W.LONG),('yppm',W.LONG),
              ('colors',W.DWORD),('important',W.DWORD)]


class Blend(C.Structure):
    _fields_=[('op',W.BYTE),('flags',W.BYTE),('alpha',W.BYTE),('format',W.BYTE)]


class LayeredOrb:
    def __init__(self,window):
        self.window=window
        self.user=C.WinDLL('user32',use_last_error=True)
        self.gdi=C.WinDLL('gdi32',use_last_error=True)
        signatures={
            'GetAncestor':([W.HWND,W.UINT],W.HWND),
            'GetWindowRect':([W.HWND,C.POINTER(W.RECT)],W.BOOL),
            'GetWindowLongW':([W.HWND,C.c_int],W.LONG),
            'SetWindowLongW':([W.HWND,C.c_int,W.LONG],W.LONG),
            'UpdateLayeredWindow':([W.HWND,W.HDC,C.POINTER(W.POINT),C.POINTER(W.SIZE),W.HDC,C.POINTER(W.POINT),W.DWORD,C.POINTER(Blend),W.DWORD],W.BOOL),
        }
        for name,(args,result) in signatures.items():
            fn=getattr(self.user,name);fn.argtypes=args;fn.restype=result
        for name,args,result in [
            ('CreateCompatibleDC',[W.HDC],W.HDC),
            ('CreateDIBSection',[W.HDC,C.POINTER(BitmapHeader),W.UINT,C.POINTER(C.c_void_p),W.HANDLE,W.DWORD],W.HBITMAP),
            ('SelectObject',[W.HDC,W.HANDLE],W.HANDLE),
            ('DeleteObject',[W.HANDLE],W.BOOL),('DeleteDC',[W.HDC],W.BOOL)]:
            fn=getattr(self.gdi,name);fn.argtypes=args;fn.restype=result
        self.hwnd=self.user.GetAncestor(window.winfo_id(),2)
        self.key=None;self.pixels=None;self.fonts={};self.last_alpha=None

    def present(self,level,ready,hover,text,alpha):
        rect=W.RECT()
        if not self.user.GetWindowRect(self.hwnd,C.byref(rect)):
            raise C.WinError(C.get_last_error())
        width=rect.right-rect.left;height=rect.bottom-rect.top
        if width<2 or height<2:return
        key=(width,height,level,ready,hover,text)
        if key!=self.key:
            image=artwork(width,level,ready,hover).copy()
            if height!=width:image=image.resize((width,height))
            size=max(9,round(width*10/56))
            if size not in self.fonts:
                import os
                self.fonts[size]=ImageFont.truetype(os.path.join(os.environ.get('WINDIR','C:/Windows'),'Fonts','segoeuib.ttf'),size)
            ImageDraw.Draw(image).text((width/2,height*41/56),text,font=self.fonts[size],fill='#ddd9f5',anchor='mm')
            # Pillow's RGBa mode premultiplies each color channel by alpha.
            self.pixels=image.convert('RGBa').tobytes('raw','BGRa')
            self.key=key
        dc=self.gdi.CreateCompatibleDC(None)
        bitmap=None;old=None
        try:
            header=BitmapHeader(C.sizeof(BitmapHeader),width,-height,1,32,0,0,0,0,0,0)
            bits=C.c_void_p()
            bitmap=self.gdi.CreateDIBSection(dc,C.byref(header),0,C.byref(bits),None,0)
            if not bitmap or not bits.value:raise C.WinError(C.get_last_error())
            C.memmove(bits,self.pixels,len(self.pixels))
            old=self.gdi.SelectObject(dc,bitmap)
            # Tk may have used SetLayeredWindowAttributes for global opacity.
            # Reset its layered style before supplying per-pixel alpha.
            blend=Blend(0,0,max(1,min(255,round(alpha*255))),1)
            size=W.SIZE(width,height);origin=W.POINT(0,0)
            if not self.user.UpdateLayeredWindow(self.hwnd,None,None,C.byref(size),dc,C.byref(origin),0,C.byref(blend),2):
                style=self.user.GetWindowLongW(self.hwnd,-20)
                self.user.SetWindowLongW(self.hwnd,-20,style & ~0x80000)
                self.user.SetWindowLongW(self.hwnd,-20,style | 0x80000)
                if not self.user.UpdateLayeredWindow(self.hwnd,None,None,C.byref(size),dc,C.byref(origin),0,C.byref(blend),2):
                    raise C.WinError(C.get_last_error())
            self.last_alpha=blend.alpha
        finally:
            if old:self.gdi.SelectObject(dc,old)
            if bitmap:self.gdi.DeleteObject(bitmap)
            if dc:self.gdi.DeleteDC(dc)
