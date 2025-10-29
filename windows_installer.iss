; BactoCloud Downloader Installer Script for Inno Setup

[Setup]
AppName=BactoCloud Downloader
AppVersion=1.0.0
DefaultDirName={pf}\BactoCloudDownloader
DefaultGroupName=BactoCloud Downloader
OutputDir=Output
OutputBaseFilename=BactoCloudDownloader-Setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\BactoCloudDownloader.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\BactoCloud Downloader"; Filename: "{app}\BactoCloudDownloader.exe"
Name: "{userdesktop}\BactoCloud Downloader"; Filename: "{app}\BactoCloudDownloader.exe"

[Run]
Filename: "{app}\BactoCloudDownloader.exe"; Description: "Launch BactoCloud Downloader"; Flags: postinstall nowait skipifsilent
