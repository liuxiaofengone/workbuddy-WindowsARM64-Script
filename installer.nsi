; WorkBuddy Windows ARM64 NSIS Installer Script (UTF-8 BOM Standard)
Unicode true
SetCompressor zlib

!include "MUI2.nsh"
!include "FileFunc.nsh"

Name "WorkBuddy"
Caption "WorkBuddy 5.3.12.35805101 安装向导"
OutFile "c:\Developer\Personal\workbuddy-windowsarm64\dist\WorkBuddy Setup 5.3.12.35805101 (ARM64).exe"
InstallDir "$LOCALAPPDATA\Programs\WorkBuddy"
InstallDirRegKey HKCU "Software\WorkBuddy" "InstallLocation"
RequestExecutionLevel user

; MUI Settings
!define MUI_ICON "c:\Developer\Personal\workbuddy-windowsarm64\icon.ico"
!define MUI_UNICON "c:\Developer\Personal\workbuddy-windowsarm64\icon.ico"
!define MUI_ABORTWARNING

; Pages
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\WorkBuddy.exe"
!define MUI_FINISHPAGE_RUN_TEXT "运行 WorkBuddy"
!insertmacro MUI_PAGE_FINISH

; Uninstaller Pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  
  ; Auto-detect installed version and run silent uninstall before installing new version
  ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WorkBuddy" "UninstallString"
  ReadRegStr $1 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WorkBuddy" "DisplayVersion"
  
  IfFileExists "$0" 0 +4
    DetailPrint "正在安全卸载旧版本 WorkBuddy (v$1)..."
    ExecWait '"$0" /S _?=$INSTDIR'
    Sleep 1000

  ; Stop all running WorkBuddy processes before file extraction
  ExecWait 'taskkill /F /T /IM WorkBuddy.exe'
  ExecWait 'taskkill /F /T /IM WorkBuddyRepair.exe'
  ExecWait 'taskkill /F /T /IM qm-helper.exe'
  ExecWait 'taskkill /F /T /IM editor_sdk.exe'
  ExecWait 'taskkill /F /T /IM wechatpay-cli.exe'
  ExecWait 'taskkill /F /T /IM agently-cli.exe'
  Sleep 1000
  
  ; Extract all application files
  File /r "c:\Developer\Personal\workbuddy-windowsarm64\WorkBuddy-win32-arm64\*.*"
  
  ; Create Shortcuts
  CreateDirectory "$SMPROGRAMS\WorkBuddy"
  CreateShortCut "$SMPROGRAMS\WorkBuddy\WorkBuddy.lnk" "$INSTDIR\WorkBuddy.exe" "" "$INSTDIR\icon.ico" 0
  CreateShortCut "$DESKTOP\WorkBuddy.lnk" "$INSTDIR\WorkBuddy.exe" "" "$INSTDIR\icon.ico" 0
  
  ; Register Uninstaller in Registry
  WriteUninstaller "$INSTDIR\Uninstall WorkBuddy.exe"
  WriteRegStr HKCU "Software\WorkBuddy" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WorkBuddy" "DisplayName" "WorkBuddy"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WorkBuddy" "DisplayVersion" "5.3.12.35805101"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WorkBuddy" "Publisher" "Tencent Technology (Shenzhen) Company Limited"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WorkBuddy" "UninstallString" '"$INSTDIR\Uninstall WorkBuddy.exe"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WorkBuddy" "DisplayIcon" "$INSTDIR\WorkBuddy.exe"
SectionEnd

Section "Uninstall"
  ExecWait 'taskkill /F /T /IM WorkBuddy.exe'
  ExecWait 'taskkill /F /T /IM WorkBuddyRepair.exe'
  ExecWait 'taskkill /F /T /IM qm-helper.exe'
  
  RMDir /r "$INSTDIR"
  RMDir /r "$SMPROGRAMS\WorkBuddy"
  Delete "$DESKTOP\WorkBuddy.lnk"
  
  DeleteRegKey HKCU "Software\WorkBuddy"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\WorkBuddy"
SectionEnd
