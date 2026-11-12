# -*- mode: python ; coding: utf-8 -*-
# Portable build: ONE standalone .exe (no zip)
from PyInstaller.utils.hooks import collect_all
d, b, h = collect_all('imageio_ffmpeg')
for _m in ('edge_tts', 'certifi', 'aiohttp', 'yarl', 'multidict', 'frozenlist', 'propcache', 'aiosignal', 'aiohappyeyeballs'):
    _d, _b, _h = collect_all(_m)
    d += _d; b += _b; h += _h
a = Analysis(['gaechu_trass.py'],
             datas=[('assets', 'assets'), ('fonts', 'fonts'), ('piper_win', 'piper')] + d,
             binaries=b,
             hiddenimports=['PIL.ImageTk', 'windnd', 'winsound', 'wave', 'edge_tts', 'aiohttp', 'certifi', 'tabulate'] + h,
             excludes=['matplotlib', 'scipy', 'pandas', 'IPython', 'pytest', 'torch', 'cv2'],
             noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='EPISODIA-PORTABLE', console=False, upx=False,
          runtime_tmpdir=None, version='version.txt', icon=['assets/logo.ico'])
