#define MyAppName "DICOM Clair"
#define MyAppVersion "3.0.0"
#define MyAppExeName "DICOM Clair.exe"
[Setup]
AppId={{E9513CE2-DAF4-43B2-8671-A12C4B993300}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installateur
OutputBaseFilename=DICOM-Clair-Setup-Windows10-x64
Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayName={#MyAppName}
[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le bureau"; GroupDescription: "Icônes :"; Flags: checkedonce
[Files]
Source: "dist\DICOM Clair\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\DICOM Clair"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\DICOM Clair"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer DICOM Clair"; Flags: nowait postinstall skipifsilent
