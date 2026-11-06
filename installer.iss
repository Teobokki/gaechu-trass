#define MyVer "1.0.0"
[Setup]
AppId={{09A0D0B7-E132-4385-B05F-6E708A3A15B7}
AppName=개추 트래스
AppVersion={#MyVer}
AppVerName=개추 트래스 {#MyVer}
AppPublisher=EX Inc./HYPERION DIGITAL
AppPublisherURL=https://github.com/Teobokki/gaechu-trass
AppCopyright=©2026 EX Inc./HYPERION DIGITAL ©2026
VersionInfoVersion={#MyVer}.0
VersionInfoCompany=EX Inc.
VersionInfoCopyright=©2026 EX Inc./HYPERION DIGITAL ©2026
VersionInfoProductName=개추 트래스
VersionInfoDescription=개추 트래스 Setup
DefaultDirName={localappdata}\Programs\개추 트래스
DefaultGroupName=개추 트래스
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=GAECHU-TRASS-Setup-{#MyVer}
SetupIconFile=assets\logo.ico
UninstallDisplayIcon={app}\개추 트래스.exe
UninstallDisplayName=개추 트래스
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

[Files]
Source: "dist\개추 트래스\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\개추 트래스"; Filename: "{app}\개추 트래스.exe"; IconFilename: "{app}\개추 트래스.exe"
Name: "{group}\Uninstall 개추 트래스"; Filename: "{uninstallexe}"
Name: "{userdesktop}\개추 트래스"; Filename: "{app}\개추 트래스.exe"; IconFilename: "{app}\개추 트래스.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\개추 트래스.exe"; Description: "개추 트래스 실행"; Flags: nowait postinstall skipifsilent
