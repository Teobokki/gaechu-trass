#!/bin/sh
# ONE Windows build: PyInstaller onedir -> Inno Setup installer, plus ONE standalone portable .exe (no zip)
set -e
export PATH=/workspace/wine-portable/current/bin:$PATH WINEPREFIX=/workspace/exwifi/.wine WINEDEBUG=-all
cd /workspace/gaechu-trass
V=1.1.2
rm -rf build "dist/EPISODIA" dist/EPISODIA-PORTABLE.exe
wine 'C:\Python311\python.exe' -m PyInstaller --noconfirm "EPISODIA.spec" > pyi.log 2>&1; echo PYI_DONE
wine 'C:\InnoSetup\ISCC.exe' installer.iss > iss.log 2>&1; echo ISS_DONE
wine 'C:\Python311\python.exe' -m PyInstaller --noconfirm "EPISODIA Portable.spec" > pyi_portable.log 2>&1; echo PYI_PORTABLE_DONE
mv -f dist/EPISODIA-PORTABLE.exe "dist/EPISODIA-$V-Portable.exe"
cd dist && ls -la "EPISODIA-Setup-$V.exe" "EPISODIA-$V-Portable.exe"
sha256sum "EPISODIA-Setup-$V.exe" "EPISODIA-$V-Portable.exe"
