; =====================================================================
; Inno Setup 6 Script for WinTokenMon for Windows
; Version is injected by scripts/build_installer.py via /DMyAppVersion;
; the default below is only a fallback for manual ISCC runs.
; =====================================================================

#define MyAppName "WinTokenMon"
#ifndef MyAppVersion
#define MyAppVersion "1.0.0"
#endif
#define MyAppPublisher "WinTokenMon Contributors"
#define MyAppURL "https://github.com/JustALearner101/WinTokenMon"
#define MyAppExeName "WinTokenMon-v" + MyAppVersion + "-Portable.exe"

[Setup]
; Unique Application ID
AppId={{E5B239C8-8271-4A59-B87A-28FE1C2956D3}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Destination Directory & Group Settings
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableDirPage=no
DisableProgramGroupPage=no
AllowNoIcons=yes

; Documentation & Legal Agreements in Wizard
LicenseFile=LICENSE
InfoBeforeFile=DISCLAIMER.md

; Build Output
OutputDir=dist
OutputBaseFilename=WinTokenMon-Setup-v{#MyAppVersion}
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\assets\icon.ico
UninstallDisplayName={#MyAppName}

; Compression & Modern Wizard Styling
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "autostart"; Description: "Launch WinTokenMon automatically when Windows starts"; GroupDescription: "Startup Options:"

[Files]
; Main Executable
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Static Assets (Icons, Cries, Sprites)
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
; Documentation & Configuration Templates
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "DISCLAIMER.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: ".env.example"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu Shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"; Comment: "Universal local AI token usage monitor & desktop pet"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; Desktop Shortcut
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"; Tasks: desktopicon; Comment: "Universal local AI token usage monitor & desktop pet"

[Registry]
; Auto-start on Windows boot registry key if selected in wizard
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
; Option to launch application immediately after setup finishes
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up runtime logs and temporary files created in app directory
Type: files; Name: "{app}\debug.log"
Type: files; Name: "{app}\.env"

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
  PromptMsg: String;
begin
  if CurUninstallStep = usUninstall then
  begin
    DataDir := ExpandConstant('{userappdata}\WinTokenMon');
    if DirExists(DataDir) then
    begin
      PromptMsg := 'Do you also want to delete all saved Pokémon progress, Pokédex captures, and cached data?' + #13#10 + #13#10 +
                   'Location: ' + DataDir + #13#10 + #13#10 +
                   '• Click [Yes] to completely wipe all data.' + #13#10 +
                   '• Click [No] to keep your Pokémon save game (recommended if reinstalling later).';
      if MsgBox(PromptMsg, mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
      begin
        DelTree(DataDir, True, True, True);
      end;
    end;
  end;
end;
