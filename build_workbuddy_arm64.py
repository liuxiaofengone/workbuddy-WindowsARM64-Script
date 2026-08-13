#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
WorkBuddy Windows ARM64 Native Automated Build Script
================================================================================
Author: Antigravity AI & WorkBuddy Porting Project
Description:
    Fully automated toolchain to detect, download, unpack, patch native C++ addons
    (better-sqlite3, ripgrep), embed PE header icons, and build a native Windows
    ARM64 installer package for WorkBuddy Desktop.

Usage:
    python build_workbuddy_arm64.py [--proxy http://127.0.0.1:7890] [--skip-download]
================================================================================
"""

import os
import sys
import shutil
import zipfile
import tarfile
import json
import struct
import subprocess
import argparse
import codecs
import pathlib
import urllib.request
from typing import Optional, Dict, Tuple

# Configuration Defaults
DEFAULT_PROXY = "http://127.0.0.1:7890"
UPDATE_API_CN = "https://www.workbuddy.cn/v2/update?platform=workbuddy-win32-x64-user"
UPDATE_API_INTL = "https://www.workbuddy.ai/v2/update?platform=workbuddy-win32-x64-user"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = os.path.join(BASE_DIR, "build_workspace")
CACHE_DIR = os.path.join(BASE_DIR, "cache")
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_TOOLS_DIR = os.path.join(BASE_DIR, "build_sqlite")
TARGET_ARM64_DIR = os.path.join(BASE_DIR, "WorkBuddy-win32-arm64")

def print_header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def setup_proxy(proxy_url: Optional[str]):
    if proxy_url and proxy_url.strip():
        print(f"[+] Setting HTTP/HTTPS Proxy: {proxy_url}")
        os.environ["HTTP_PROXY"] = proxy_url
        os.environ["HTTPS_PROXY"] = proxy_url
        os.environ["http_proxy"] = proxy_url
        os.environ["https_proxy"] = proxy_url
        proxy_handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
        opener = urllib.request.build_opener(proxy_handler)
        urllib.request.install_opener(opener)
    else:
        print("[*] Direct Connection (No proxy configured).")

def download_file(url: str, target_path: str):
    print(f"[*] Downloading: {url}")
    print(f"    -> Destination: {target_path}")
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req) as resp, open(target_path, 'wb') as out_f:
        total_length = resp.headers.get('content-length')
        if total_length:
            total_length = int(total_length)
            downloaded = 0
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                downloaded += len(chunk)
                out_f.write(chunk)
                percent = (downloaded / total_length) * 100
                sys.stdout.write(f"\r    Progress: {percent:.1f}% ({downloaded / (1024*1024):.1f} MB / {total_length / (1024*1024):.1f} MB)")
                sys.stdout.flush()
            print()
        else:
            shutil.copyfileobj(resp, out_f)
    print(f"[+] Download complete. ({os.path.getsize(target_path)} bytes)")

def find_makensis() -> Optional[str]:
    in_path = shutil.which("makensis")
    if in_path:
        return in_path
    
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        cache_dir = os.path.join(local_app_data, "electron-builder", "Cache", "nsis")
        if os.path.exists(cache_dir):
            for root, dirs, files in os.walk(cache_dir):
                if "makensis.exe" in files:
                    return os.path.join(root, "makensis.exe")
    return None

def check_prerequisites():
    print_header("Step 0: Checking System Environment & Prerequisites")
    
    # 1. Python check
    print(f"[+] Python Version: {sys.version.split()[0]} ({platform_arch()})")
    
    # 2. Node.js check
    try:
        node_ver = subprocess.check_output(["node", "-v"], text=True).strip()
        print(f"[+] Node.js Version: {node_ver}")
    except Exception:
        print("[!] ERROR: Node.js is not installed or not in PATH! Node.js 18+ is required.")
        sys.exit(1)
        
    # 3. npm check
    try:
        npm_ver = subprocess.check_output(["npm", "-v"], shell=True, text=True).strip()
        print(f"[+] npm Version: {npm_ver}")
    except Exception as e:
        print(f"[!] ERROR: npm execution failed: {e}")
        sys.exit(1)
        
    # 4. NSIS (makensis.exe) check
    makensis_path = find_makensis()
    if makensis_path:
        print(f"[+] NSIS Compiler Found: {makensis_path}")
    else:
        print("[!] WARNING: makensis.exe not found in PATH or standard Electron-Builder cache!")
        print("    The script will attempt to locate it or build target binaries.")
        
    # 5. 7-Zip check
    has_7z = shutil.which("7z") or shutil.which("7za")
    if has_7z:
        print(f"[+] 7-Zip CLI Found: {has_7z}")
    else:
        print("[+] 7-Zip CLI not found in PATH, fallback to Python/PowerShell unpacker.")

def platform_arch() -> str:
    machine = struct.calcsize("P") * 8
    return "ARM64" if "ARM64" in sys.version.upper() or "AARCH64" in sys.version.upper() else f"x{machine}"

def parse_version_tuple(ver_str: str) -> tuple:
    import re
    digits = re.findall(r'\d+', ver_str)
    return tuple(int(d) for d in digits)

def compare_versions(ver1: str, ver2: str) -> int:
    t1 = parse_version_tuple(ver1)
    t2 = parse_version_tuple(ver2)
    if t1 > t2:
        return 1
    elif t1 < t2:
        return -1
    else:
        return 0

def get_installed_workbuddy_version() -> Tuple[Optional[str], Optional[str]]:
    """Returns (version_string, install_path) of currently installed WorkBuddy on Windows."""
    # 1. Query Windows Registry
    import winreg
    keys = [
        (winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Uninstall\WorkBuddy'),
        (winreg.HKEY_LOCAL_MACHINE, r'Software\Microsoft\Windows\CurrentVersion\Uninstall\WorkBuddy')
    ]
    for root, path in keys:
        try:
            with winreg.OpenKey(root, path) as k:
                ver, _ = winreg.QueryValueEx(k, 'DisplayVersion')
                inst_dir, _ = winreg.QueryValueEx(k, 'InstallLocation')
                if ver:
                    return str(ver), str(inst_dir)
        except Exception:
            pass
            
    # 2. Fallback check local appdata directory
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        app_asar = os.path.join(local_app_data, "Programs", "WorkBuddy", "resources", "app.asar")
        if os.path.exists(app_asar):
            with open(app_asar, 'rb') as f:
                content = f.read()
                pkg_idx = content.find(b'"version"')
                if pkg_idx != -1:
                    snippet = content[pkg_idx:pkg_idx+200].decode('utf-8', errors='ignore')
                    import re
                    m = re.search(r'"version"\s*:\s*"([0-9\.]+)"', snippet)
                    if m:
                        return m.group(1), os.path.dirname(os.path.dirname(app_asar))
            
    return None, None

def fetch_latest_release_info() -> Tuple[str, str]:
    print_header("Step 1: Detecting Latest WorkBuddy Release Info")
    print(f"[*] Querying API: {UPDATE_API_CN}")
    try:
        req = urllib.request.Request(UPDATE_API_CN, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            version = data.get("version", "5.3.5")
            url = data.get("url", "")
            print(f"[+] Latest Release Version: {version}")
            print(f"[+] Direct Download URL: {url}")
            return version, url
    except Exception as e:
        print(f"[!] Primary API failed ({e}), trying fallback API: {UPDATE_API_INTL}")
        req = urllib.request.Request(UPDATE_API_INTL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            version = data.get("version", "5.3.5")
            url = data.get("url", "")
            print(f"[+] Latest Release Version: {version}")
            print(f"[+] Direct Download URL: {url}")
            return version, url

def unpack_installer(installer_exe: str, extract_to: str):
    print_header("Step 2: Unpacking WorkBuddy x64 Installer Package")
    os.makedirs(extract_to, exist_ok=True)
    
    # Method 1: Try 7-Zip CLI if available
    has_7z = shutil.which("7z") or shutil.which("7za")
    if has_7z:
        print("[*] Unpacking installer executable using 7-Zip CLI...")
        subprocess.run([has_7z, "x", "-y", f"-o{extract_to}", installer_exe], check=True)
    else:
        print("[*] Unpacking installer using PowerShell Expand/7z...")
        ps_cmd = f"& {{ Expand-Archive -Path '{installer_exe}' -DestinationPath '{extract_to}' -Force }}"
        try:
            subprocess.run(["powershell", "-Command", ps_cmd], check=True)
        except Exception:
            print("[!] PowerShell Expand failed, 7-Zip CLI is recommended.")
            sys.exit(1)

    # Search recursively for inner app-64.7z archive
    app_7z_path = None
    for r, d, files in os.walk(extract_to):
        if "app-64.7z" in files:
            app_7z_path = os.path.join(r, "app-64.7z")
            break
            
    if app_7z_path and has_7z:
        print(f"[*] Unpacking inner app-64.7z archive from: {app_7z_path} ...")
        subprocess.run([has_7z, "x", "-y", f"-o{extract_to}", app_7z_path], check=True)
    print(f"[+] Unpacked installer successfully into: {extract_to}")

def find_resources_dir(base_extract_dir: str) -> str:
    for r, dirs, files in os.walk(base_extract_dir):
        if "resources" in dirs and os.path.exists(os.path.join(r, "resources", "app.asar")):
            return os.path.join(r, "resources")
        if os.path.basename(r) == "resources" and "app.asar" in files:
            return r
    target_res = os.path.join(base_extract_dir, "resources")
    os.makedirs(target_res, exist_ok=True)
    return target_res

def get_electron_version(resources_dir: str) -> str:
    app_asar = os.path.join(resources_dir, "app.asar")
    if not os.path.exists(app_asar):
        return "37.10.3"
        
    print("[*] Inspecting app.asar for Electron version...")
    # Extract package.json from app.asar using Python
    with open(app_asar, 'rb') as f:
        content = f.read()
        pkg_idx = content.find(b'"devDependencies"')
        if pkg_idx != -1:
            snippet = content[pkg_idx:pkg_idx+500].decode('utf-8', errors='ignore')
            import re
            m = re.search(r'"electron"\s*:\s*"([^"]+)"', snippet)
            if m:
                ver = m.group(1).lstrip("^~")
                print(f"[+] Detected Electron Version from package.json: {ver}")
                return ver
    return "37.10.3"

def build_better_sqlite3_arm64(electron_version: str):
    print_header("Step 3: Compiling Native better-sqlite3 12.8.0 for Windows ARM64")
    os.makedirs(BUILD_TOOLS_DIR, exist_ok=True)
    
    # 1. Install better-sqlite3@12.8.0 & rcedit & @electron/rebuild in build_sqlite
    print("[*] Installing better-sqlite3@12.8.0, rcedit and @electron/rebuild in helper workspace...")
    subprocess.run(
        ["npm", "install", "better-sqlite3@12.8.0", "rcedit", "@electron/rebuild", "--legacy-peer-deps"],
        cwd=BUILD_TOOLS_DIR,
        shell=True,
        check=True
    )
    
    # 2. Rebuild better-sqlite3 for target Electron version & win32-arm64
    print(f"[*] Rebuilding better-sqlite3 for Electron {electron_version} (win32-arm64)...")
    rebuild_cmd = f"npx @electron/rebuild -v {electron_version} -f -w better-sqlite3"
    subprocess.run(rebuild_cmd, cwd=BUILD_TOOLS_DIR, shell=True, check=True)
    
    compiled_node = os.path.join(BUILD_TOOLS_DIR, r"node_modules\better-sqlite3\build\Release\better_sqlite3.node")
    if not os.path.exists(compiled_node):
        print(f"[!] ERROR: Compiled node addon not found at {compiled_node}")
        sys.exit(1)
        
    print(f"[+] Successfully compiled better_sqlite3.node for ARM64: {compiled_node}")

def prepare_arm64_runtime(electron_version: str, source_extracted_dir: str):
    print_header("Step 4: Assembling WorkBuddy ARM64 Standalone Directory")
    
    if os.path.exists(TARGET_ARM64_DIR):
        print(f"[*] Cleaning previous target directory: {TARGET_ARM64_DIR}")
        shutil.rmtree(TARGET_ARM64_DIR)
    os.makedirs(TARGET_ARM64_DIR, exist_ok=True)
    
    # 1. Download & Extract Electron win32-arm64 runtime
    electron_zip = os.path.join(CACHE_DIR, f"electron-v{electron_version}-win32-arm64.zip")
    electron_url = f"https://github.com/electron/electron/releases/download/v{electron_version}/electron-v{electron_version}-win32-arm64.zip"
    mirror_url = f"https://npmmirror.com/mirrors/electron/v{electron_version}/electron-v{electron_version}-win32-arm64.zip"
    
    if not os.path.exists(electron_zip):
        try:
            download_file(electron_url, electron_zip)
        except Exception as e:
            print(f"[!] GitHub download failed ({e}), fallback to npmmirror...")
            download_file(mirror_url, electron_zip)
            
    print(f"[*] Extracting Electron {electron_version} ARM64 runtime...")
    with zipfile.ZipFile(electron_zip, 'r') as z:
        z.extractall(TARGET_ARM64_DIR)
        
    # Rename electron.exe -> WorkBuddy.exe
    old_exe = os.path.join(TARGET_ARM64_DIR, "electron.exe")
    new_exe = os.path.join(TARGET_ARM64_DIR, "WorkBuddy.exe")
    if os.path.exists(old_exe):
        os.rename(old_exe, new_exe)
        print("[+] Renamed electron.exe -> WorkBuddy.exe")
        
    # 2. Embed official WorkBuddy icon and Version Info into WorkBuddy.exe PE Header via rcedit
    icon_path = os.path.join(BASE_DIR, "icon.ico")
    if os.path.exists(icon_path):
        print(f"[*] Embedding PE Header Icon & Version Strings: {icon_path} -> WorkBuddy.exe")
        new_exe_posix = pathlib.Path(new_exe).as_posix()
        icon_posix = pathlib.Path(icon_path).as_posix()
        node_cmd = f"const {{ rcedit }} = require('rcedit'); rcedit('{new_exe_posix}', {{ icon: '{icon_posix}', 'version-string': {{ CompanyName: 'Tencent Technology (Shenzhen) Company Limited', FileDescription: 'WorkBuddy Desktop - AI Agent Desktop Application', LegalCopyright: 'Copyright 2026 Tencent Technology (Shenzhen) Company Limited', ProductName: 'WorkBuddy', InternalName: 'WorkBuddy.exe', OriginalFilename: 'WorkBuddy.exe' }} }});"
        subprocess.run(["node", "-e", node_cmd], cwd=BUILD_TOOLS_DIR, check=True)
        print("[+] Embedded official WorkBuddy Icon & Version Metadata into WorkBuddy.exe PE Header!")
        shutil.copy(icon_path, os.path.join(TARGET_ARM64_DIR, "icon.ico"))
        
    # 3. Copy app resources from unpacked x64
    src_resources = find_resources_dir(source_extracted_dir)
    dst_resources = os.path.join(TARGET_ARM64_DIR, "resources")
    print(f"[*] Copying app resources: {src_resources} -> {dst_resources}")
    shutil.copytree(src_resources, dst_resources, dirs_exist_ok=True)
    
    # 4. Patch compiled ARM64 better_sqlite3.node
    compiled_node = os.path.join(BUILD_TOOLS_DIR, r"node_modules\better-sqlite3\build\Release\better_sqlite3.node")
    with open(compiled_node, 'rb') as f:
        node_bytes = f.read()
        
    target_node = os.path.join(dst_resources, r"app.asar.unpacked\node_modules\better-sqlite3\build\Release\better_sqlite3.node")
    os.makedirs(os.path.dirname(target_node), exist_ok=True)
    with open(target_node, 'wb') as f:
        f.write(node_bytes)
    print(f"[+] Patched ARM64 better_sqlite3.node -> {target_node}")
    
    # 5. Download & Patch ARM64 ripgrep (rg.exe)
    rg_zip = os.path.join(CACHE_DIR, "ripgrep-v15.0.1-aarch64-pc-windows-msvc.zip")
    rg_url = "https://github.com/microsoft/ripgrep-prebuilt/releases/download/v15.0.1/ripgrep-v15.0.1-aarch64-pc-windows-msvc.zip"
    if not os.path.exists(rg_zip):
        download_file(rg_url, rg_zip)
        
    rg_bytes = None
    with zipfile.ZipFile(rg_zip, 'r') as z:
        for name in z.namelist():
            if name.endswith("rg.exe"):
                rg_bytes = z.read(name)
                break
    if rg_bytes:
        target_rg = os.path.join(dst_resources, r"app.asar.unpacked\cli\vendor\ripgrep\x64-win32\rg.exe")
        os.makedirs(os.path.dirname(target_rg), exist_ok=True)
        with open(target_rg, 'wb') as f:
            f.write(rg_bytes)
        print(f"[+] Patched ARM64 rg.exe -> {target_rg}")
        
    # 6. Patch app.asar with custom ARM64 in-app update handler
    target_app_asar = os.path.join(dst_resources, "app.asar")
    from patch_asar_win32_updater import patch_app_asar_win32_updater
    print(f"[*] Applying ARM64 In-App Update Handler patch to app.asar...")
    patch_app_asar_win32_updater(target_app_asar)
    
    # 7. Embed ARM64 Updater Toolchain into $INSTDIR/tools/arm64_updater/
    tools_updater_dir = os.path.join(TARGET_ARM64_DIR, "tools", "arm64_updater")
    print(f"[*] Embedding ARM64 Updater Toolchain -> {tools_updater_dir}")
    os.makedirs(tools_updater_dir, exist_ok=True)
    
    files_to_embed = [
        "build_workbuddy_arm64.py",
        "build.bat",
        "icon.ico",
        "patch_asar_win32_updater.py",
        "create_bulletproof_bat.py",
        "README_BUILD.md",
        "README.md"
    ]
    for f in files_to_embed:
        src = os.path.join(BASE_DIR, f)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(tools_updater_dir, f))
    print("[+] Successfully embedded ARM64 Updater Toolchain into installation directory!")

def generate_nsi_script(version: str) -> str:
    print_header("Step 5: Generating NSIS Installer Script (UTF-8 BOM)")
    nsi_path = os.path.join(BASE_DIR, "installer.nsi")
    dist_setup_exe = os.path.join(DIST_DIR, f"WorkBuddy Setup {version} (ARM64).exe")
    os.makedirs(DIST_DIR, exist_ok=True)
    
    icon_path = os.path.join(BASE_DIR, "icon.ico")
    
    nsi_content = f"""\
; WorkBuddy Windows ARM64 NSIS Installer Script (UTF-8 BOM Standard)
Unicode true
SetCompressor zlib

!include "MUI2.nsh"
!include "FileFunc.nsh"

Name "WorkBuddy"
Caption "WorkBuddy {version} 安装向导"
OutFile "{dist_setup_exe}"
InstallDir "$LOCALAPPDATA\\Programs\\WorkBuddy"
InstallDirRegKey HKCU "Software\\WorkBuddy" "InstallLocation"
RequestExecutionLevel user

; MUI Settings
!define MUI_ICON "{icon_path}"
!define MUI_UNICON "{icon_path}"
!define MUI_ABORTWARNING

; Pages
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\\WorkBuddy.exe"
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
  ReadRegStr $0 HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\WorkBuddy" "UninstallString"
  ReadRegStr $1 HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\WorkBuddy" "DisplayVersion"
  
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
  File /r "{TARGET_ARM64_DIR}\\*.*"
  
  ; Create Shortcuts
  CreateDirectory "$SMPROGRAMS\\WorkBuddy"
  CreateShortCut "$SMPROGRAMS\\WorkBuddy\\WorkBuddy.lnk" "$INSTDIR\\WorkBuddy.exe" "" "$INSTDIR\\icon.ico" 0
  CreateShortCut "$DESKTOP\\WorkBuddy.lnk" "$INSTDIR\\WorkBuddy.exe" "" "$INSTDIR\\icon.ico" 0
  
  ; Register Uninstaller in Registry
  WriteUninstaller "$INSTDIR\\Uninstall WorkBuddy.exe"
  WriteRegStr HKCU "Software\\WorkBuddy" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\WorkBuddy" "DisplayName" "WorkBuddy"
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\WorkBuddy" "DisplayVersion" "{version}"
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\WorkBuddy" "Publisher" "Tencent Technology (Shenzhen) Company Limited"
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\WorkBuddy" "UninstallString" '"$INSTDIR\\Uninstall WorkBuddy.exe"'
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\WorkBuddy" "DisplayIcon" "$INSTDIR\\WorkBuddy.exe"
SectionEnd

Section "Uninstall"
  ExecWait 'taskkill /F /T /IM WorkBuddy.exe'
  ExecWait 'taskkill /F /T /IM WorkBuddyRepair.exe'
  ExecWait 'taskkill /F /T /IM qm-helper.exe'
  
  RMDir /r "$INSTDIR"
  RMDir /r "$SMPROGRAMS\\WorkBuddy"
  Delete "$DESKTOP\\WorkBuddy.lnk"
  
  DeleteRegKey HKCU "Software\\WorkBuddy"
  DeleteRegKey HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\WorkBuddy"
SectionEnd
"""
    with open(nsi_path, 'wb') as f:
        f.write(codecs.BOM_UTF8)
        f.write(nsi_content.encode('utf-8'))
        
    print(f"[+] Generated installer.nsi with UTF-8 BOM: {nsi_path}")
    return nsi_path

def compile_nsis_installer(nsi_script: str, version: str):
    print_header("Step 6: Compiling Final NSIS Installer Package")
    makensis = find_makensis()
    if not makensis:
        print("[!] ERROR: makensis.exe not found! Please install NSIS or run via electron-builder cache.")
        sys.exit(1)
        
    print(f"[*] Running makensis on {nsi_script} ...")
    subprocess.run([makensis, nsi_script], check=True)
    
    target_exe = os.path.join(DIST_DIR, f"WorkBuddy Setup {version} (ARM64).exe")
    if os.path.exists(target_exe):
        size_mb = os.path.getsize(target_exe) / (1024 * 1024)
        print_header(f"SUCCESS: Generated Native Windows ARM64 Installer Package!")
        print(f"[+] Output Installer Path: {target_exe}")
        print(f"[+] Package File Size: {size_mb:.1f} MB")
    else:
        print(f"[!] ERROR: Expected output executable not found: {target_exe}")

def audit_binary_architectures():
    print_header("Step 7: Verification Audit Scan of PE Binaries")
    def get_pe_arch(filepath):
        try:
            with open(filepath, 'rb') as f:
                mz = f.read(2)
                if mz != b'MZ':
                    return 'NOT_PE'
                f.seek(0x3C)
                pe_offset = struct.unpack('<I', f.read(4))[0]
                f.seek(pe_offset)
                pe_sig = f.read(4)
                if pe_sig != b'PE\x00\x00':
                    return 'INVALID_PE'
                machine = struct.unpack('<H', f.read(2))[0]
                return 'ARM64' if machine == 0xAA64 else ('x64' if machine == 0x8664 else f'0x{machine:x}')
        except Exception:
            return 'ERROR'

    arm64_binaries = []
    x64_binaries = []
    for r, d, files in os.walk(TARGET_ARM64_DIR):
        for file in files:
            if file.endswith(('.exe', '.dll', '.node')):
                full_path = os.path.join(r, file)
                rel_path = os.path.relpath(full_path, TARGET_ARM64_DIR)
                arch = get_pe_arch(full_path)
                if arch == 'ARM64':
                    arm64_binaries.append(rel_path)
                elif arch == 'x64':
                    x64_binaries.append(rel_path)
                    
    print(f"[+] Audit Summary: ARM64 Core Binaries: {len(arm64_binaries)}, Emulated x64 Subprocesses: {len(x64_binaries)}")
    print("    Key ARM64 Binaries:")
    for b in arm64_binaries[:10]:
        print(f"      - {b}")

def launch_installer(target_exe: str):
    print_header("Step 8: Auto-launching New ARM64 Installer for Smooth Upgrade")
    if os.path.exists(target_exe):
        print(f"[*] Launching new ARM64 installer package: {target_exe}")
        subprocess.Popen([target_exe], shell=True)
        print("[+] Installer launched successfully! Please follow the installer prompts.")
    else:
        print(f"[!] Target installer executable not found: {target_exe}")

def main():
    parser = argparse.ArgumentParser(description="WorkBuddy Windows ARM64 Automated Build System")
    parser.add_argument("--proxy", type=str, default="", help="HTTP/HTTPS Proxy URL (e.g. http://127.0.0.1:7890)")
    parser.add_argument("--skip-download", action="store_true", help="Skip downloading x64 installer if already present")
    parser.add_argument("--force", action="store_true", help="Force download and rebuild even if local version is up to date")
    parser.add_argument("--no-launch", action="store_true", help="Do not automatically launch the generated installer package after build completion")
    args = parser.parse_args()

    setup_proxy(args.proxy)
    check_prerequisites()
    
    online_version, download_url = fetch_latest_release_info()
    installed_version, install_path = get_installed_workbuddy_version()
    
    print_header("Version Check & Upgrade Status")
    if installed_version:
        print(f"[+] 当前系统已安装版本: v{installed_version}")
        print(f"[+] 线上最新版本:         v{online_version}")
        cmp_result = compare_versions(online_version, installed_version)
        if cmp_result > 0:
            print("\n" + "!" * 80)
            print("  [!] 检测到 WorkBuddy 有最新版本发布！")
            print(f"      线上版本 v{online_version} 高于本地已安装版本 v{installed_version}。")
            print("      提示：本升级构建完成后，将自动执行安全卸载旧版本并拉起全新 ARM64 安装程序平滑升级！")
            print("!" * 80 + "\n")
        elif cmp_result == 0:
            print(f"[*] 当前系统已安装的 WorkBuddy (v{installed_version}) 已是最新版本。")
            if not args.force and not args.skip_download:
                print("    如果您仍需重新构建原生包，请使用 --force 参数强行重新构建。")
                ans = input("是否继续重新构建原生安装包? (y/N): ").strip().lower()
                if ans != 'y':
                    print("[*] 已取消构建。")
                    sys.exit(0)
        else:
            print(f"[*] 当前系统已安装版本 (v{installed_version}) 高于或等于线上版本 (v{online_version})。")
    else:
        print(f"[+] 未检测到系统已安装的 WorkBuddy。将开始构建最新原生版本 (v{online_version})。")
    
    installer_exe = os.path.join(CACHE_DIR, f"WorkBuddy-win32-x64-user-{online_version}.exe")
    if not args.skip_download or not os.path.exists(installer_exe):
        download_file(download_url, installer_exe)
        
    extracted_dir = os.path.join(WORK_DIR, f"extracted_{online_version}")
    unpack_installer(installer_exe, extracted_dir)
    
    resources_dir = find_resources_dir(extracted_dir)
    electron_ver = get_electron_version(resources_dir)
    
    build_better_sqlite3_arm64(electron_ver)
    prepare_arm64_runtime(electron_ver, extracted_dir)
    
    nsi_script = generate_nsi_script(online_version)
    compile_nsis_installer(nsi_script, online_version)
    
    audit_binary_architectures()

    target_setup_exe = os.path.join(DIST_DIR, f"WorkBuddy Setup {online_version} (ARM64).exe")
    if not args.no_launch:
        launch_installer(target_setup_exe)

if __name__ == "__main__":
    main()
