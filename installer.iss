#define MyVer "1.1.3"
[Setup]
AppId={{09A0D0B7-E132-4385-B05F-6E708A3A15B7}
AppName=EPISODIA
AppVersion={#MyVer}
AppVerName=EPISODIA {#MyVer}
AppPublisher=EX Inc./HYPERION DIGITAL
AppPublisherURL=https://github.com/Teobokki/gaechu-trass
AppCopyright=©2026 EX Inc./HYPERION DIGITAL ©2026
VersionInfoVersion={#MyVer}.0
VersionInfoCompany=EX Inc.
VersionInfoCopyright=©2026 EX Inc./HYPERION DIGITAL ©2026
VersionInfoProductName=EPISODIA
VersionInfoDescription=EPISODIA Setup
DefaultDirName={localappdata}\Programs\EPISODIA
DefaultGroupName=EPISODIA
UsePreviousAppDir=no
UsePreviousGroup=no
DisableProgramGroupPage=yes
DisableDirPage=yes
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=EPISODIA-Setup-{#MyVer}
SetupIconFile=assets\logo.ico
UninstallDisplayIcon={app}\EPISODIA.exe
UninstallDisplayName=EPISODIA
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal"
; old name (개추 트래스, 1.0.x): remove old program folder and shortcuts
Type: filesandordirs; Name: "{localappdata}\Programs\개추 트래스"
Type: filesandordirs; Name: "{userprograms}\개추 트래스"
Type: files; Name: "{userdesktop}\개추 트래스.lnk"

[Files]
Source: "dist\EPISODIA\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\EPISODIA"; Filename: "{app}\EPISODIA.exe"; IconFilename: "{app}\EPISODIA.exe"
Name: "{group}\Uninstall EPISODIA"; Filename: "{uninstallexe}"
Name: "{userdesktop}\EPISODIA"; Filename: "{app}\EPISODIA.exe"; IconFilename: "{app}\EPISODIA.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\EPISODIA.exe"; Description: "EPISODIA 실행"; Flags: nowait postinstall skipifsilent
