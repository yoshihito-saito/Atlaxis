; Compile after PyInstaller, passing /DAppVersion from pyproject.toml.
#ifndef AppVersion
  #error AppVersion must be provided by the build command.
#endif

[Setup]
AppId=org.atlaxis.desktop
AppName=Atlaxis
AppVersion={#AppVersion}
AppPublisher=Atlaxis
DefaultDirName={localappdata}\Programs\Atlaxis
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
WizardStyle=modern
SetupIconFile=..\logo\Atlaxis.ico
UninstallDisplayIcon={app}\Atlaxis.exe
LicenseFile=..\LICENSE.md
OutputDir=..\dist
OutputBaseFilename=Atlaxis-Windows-x64-Setup
Compression=lzma2
SolidCompression=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\Atlaxis\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Atlaxis"; Filename: "{app}\Atlaxis.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Atlaxis"; Filename: "{app}\Atlaxis.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\Atlaxis.exe"; Description: "Launch Atlaxis"; Flags: nowait postinstall skipifsilent

; Intentionally no user-data/settings deletion: these belong to the user and
; are created by the app outside the installed bundle on first launch.
