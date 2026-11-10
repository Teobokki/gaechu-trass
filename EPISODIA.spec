# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
d, b, h = collect_all('imageio_ffmpeg')
for _m in ('edge_tts', 'certifi', 'aiohttp', 'yarl', 'multidict', 'frozenlist', 'propcache', 'aiosignal', 'aiohappyeyeballs'):
    _d, _b, _h = collect_all(_m)
    d += _d; b += _b; h += _h
a = Analysis(['gaechu_trass.py'],
             datas=[('assets', 'assets'), ('fonts', 'fonts')] + d,
             binaries=b,
             hiddenimports=['PIL.ImageTk', 'windnd', 'winsound', 'wave', 'edge_tts', 'aiohttp', 'certifi', 'tabulate'] + h,
             excludes=['matplotlib', 'scipy', 'pandas', 'IPython', 'pytest', 'torch', 'cv2'],
             noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='EPISODIA', console=False, upx=False,
          version='version.txt', icon=['assets/logo.ico'])
coll = COLLECT(exe, a.binaries, a.datas, upx=False, name='EPISODIA')
