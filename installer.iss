[Setup]
AppName=Fireboy Watergirl
AppVersion=1.0
DefaultDirName={pf}\FireboyWatergirl
DefaultGroupName=Fireboy Watergirl
OutputDir=installer
OutputBaseFilename=FireboyWatergirl_Installer
Compression=lzma
SolidCompression=yes
SetupIconFile=icon.ico

[Files]
Source: "dist\FireboyWatergirl\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\Fireboy Watergirl"; Filename: "{app}\FireboyWatergirl.exe"; IconFilename: "{app}\FireboyWatergirl.exe"
Name: "{commondesktop}\Fireboy Watergirl"; Filename: "{app}\FireboyWatergirl.exe"; Tasks: desktopicon; IconFilename: "{app}\FireboyWatergirl.exe"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Opciones adicionales:"
