; Inno Setup 脚本
; CAJ转换器 v1.0.1 安装程序

[Setup]
AppName=CAJ转换器
AppVersion=1.0.1
AppPublisher=鲲穹AI
AppPublisherURL=https://www.kunqiongai.com
AppSupportURL=https://www.kunqiongai.com
AppUpdatesURL=https://www.kunqiongai.com
DefaultDirName={autopf}\CAJ转换器
DefaultGroupName=CAJ转换器
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=CAJ转换器_v1.0.1_安装程序
SetupIconFile=CAJ转换器.ico
Compression=lzma
SolidCompression=yes
LanguageDetectionMethod=uilanguage
ShowLanguageDialog=no
WizardStyle=modern
UninstallDisplayIcon={app}\CAJ转换器.exe
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "dist\CAJ转换器\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\CAJ转换器\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "CAJ转换器.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "鲲穹01.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\CAJ转换器"; Filename: "{app}\CAJ转换器.exe"; IconFilename: "{app}\CAJ转换器.ico"
Name: "{group}\{cm:UninstallProgram,CAJ转换器}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\CAJ转换器"; Filename: "{app}\CAJ转换器.exe"; IconFilename: "{app}\CAJ转换器.ico"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\CAJ转换器"; Filename: "{app}\CAJ转换器.exe"; IconFilename: "{app}\CAJ转换器.ico"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\CAJ转换器.exe"; Description: "{cm:LaunchProgram,CAJ转换器}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: dirifempty; Name: "{app}"

[Code]
procedure InitializeWizard;
var
  IconPath: String;
begin
  // 尝试从临时目录加载图标，如果失败则跳过
  IconPath := ExpandConstant('{tmp}\CAJ转换器.ico');
  if FileExists(IconPath) then
  begin
    try
      WizardForm.WizardSmallBitmapImage.Bitmap.LoadFromFile(IconPath);
    except
      // 如果加载失败，继续执行，不中断安装
    end;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
end;

function BackButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpSelectDir then
  begin
    WizardForm.DirEdit.Text := ExpandConstant('{autopf}\CAJ转换器');
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // 安装完成后的操作
  end;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
end;

function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo, MemoTypeInfo,
  MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;
var
  S: String;
begin
  S := '';
  S := S + 'CAJ转换器 v1.0.0' + NewLine + NewLine;
  S := S + '安装位置:' + NewLine;
  S := S + Space + WizardForm.DirEdit.Text + NewLine + NewLine;
  S := S + '程序组:' + NewLine;
  S := S + Space + WizardForm.GroupEdit.Text + NewLine + NewLine;
  S := S + '其他选项:' + NewLine;
  if WizardForm.TasksList.Checked[0] then
    S := S + Space + '创建桌面快捷方式' + NewLine;
  if WizardForm.TasksList.Checked[1] then
    S := S + Space + '创建快速启动栏快捷方式' + NewLine;
  Result := S;
end;
