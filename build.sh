#!/bin/sh
# ONE Windows build: PyInstaller onedir -> Inno Setup installer + portable zip
set -e
export PATH=/workspace/wine-portable/current/bin:$PATH WINEPREFIX=/workspace/exwifi/.wine WINEDEBUG=-all
cd /workspace/gaechu-trass
V=1.1.1
rm -rf build "dist/EPISODIA"
wine 'C:\Python311\python.exe' -m PyInstaller --noconfirm "EPISODIA.spec" > pyi.log 2>&1; echo PYI_DONE
wine 'C:\InnoSetup\ISCC.exe' installer.iss > iss.log 2>&1; echo ISS_DONE
cd dist && rm -f EPISODIA-$V-Windows-x64.zip && python3 -c "import shutil;shutil.make_archive('EPISODIA-$V-Windows-x64','zip','.','EPISODIA')" && echo ZIP_DONE
ls -la
sha256sum EPISODIA-Setup-$V.exe EPISODIA-$V-Windows-x64.zip
