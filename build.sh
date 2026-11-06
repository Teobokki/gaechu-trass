#!/bin/sh
# ONE Windows build: PyInstaller onedir -> Inno Setup installer + portable zip
set -e
export PATH=/workspace/wine-portable/current/bin:$PATH WINEPREFIX=/workspace/exwifi/.wine WINEDEBUG=-all
cd /workspace/gaechu-trass
V=1.0.4
rm -rf build "dist/개추 트래스"
wine 'C:\Python311\python.exe' -m PyInstaller --noconfirm "개추 트래스.spec" > pyi.log 2>&1; echo PYI_DONE
wine 'C:\InnoSetup\ISCC.exe' installer.iss > iss.log 2>&1; echo ISS_DONE
cd dist && rm -f GAECHU-TRASS-$V-Windows-x64.zip && python3 -c "import shutil;shutil.make_archive('GAECHU-TRASS-$V-Windows-x64','zip','.','개추 트래스')" && echo ZIP_DONE
ls -la
sha256sum GAECHU-TRASS-Setup-$V.exe GAECHU-TRASS-$V-Windows-x64.zip
