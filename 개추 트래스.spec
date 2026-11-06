# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
d, b, h = collect_all('imageio_ffmpeg')
a = Analysis(['gaechu_trass.py'],
             datas=[('assets', 'assets'), ('fonts', 'fonts')] + d,
             binaries=b,
             hiddenimports=['PIL.ImageTk', 'windnd'] + h,
             excludes=['matplotlib', 'scipy', 'pandas', 'IPython', 'pytest', 'torch', 'cv2'],
             noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='개추 트래스', console=False, upx=False,
          version='version.txt', icon=['assets/logo.ico'])
coll = COLLECT(exe, a.binaries, a.datas, upx=False, name='개추 트래스')
