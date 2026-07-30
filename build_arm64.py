import os
import sys
import shutil
import zipfile
import tarfile
import urllib.request
import struct

# Set proxy settings as requested
PROXY = "http://127.0.0.1:7890"
os.environ["HTTP_PROXY"] = PROXY
os.environ["HTTPS_PROXY"] = PROXY
os.environ["http_proxy"] = PROXY
os.environ["https_proxy"] = PROXY

proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
opener = urllib.request.build_opener(proxy_handler)
urllib.request.install_opener(opener)

BASE_DIR = r"c:\Developer\Personal\workbuddy-windowsarm64"
SOURCE_APP_EXTRACTED = os.path.join(BASE_DIR, "app_extracted")
TARGET_ARM64_DIR = os.path.join(BASE_DIR, "WorkBuddy-win32-arm64")
CACHE_DIR = os.path.join(BASE_DIR, "cache")

os.makedirs(CACHE_DIR, exist_ok=True)
if os.path.exists(TARGET_ARM64_DIR):
    print(f"Removing existing target dir: {TARGET_ARM64_DIR}")
    shutil.rmtree(TARGET_ARM64_DIR)
os.makedirs(TARGET_ARM64_DIR, exist_ok=True)

def download_file(url, target_path):
    print(f"Downloading {url} -> {target_path} ...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp, open(target_path, 'wb') as out_f:
        shutil.copyfileobj(resp, out_f)
    print(f"Downloaded successfully ({os.path.getsize(target_path)} bytes).")

print("=== Step 1: Downloading & Extracting Electron v37.10.3 (win32-arm64) ===")
electron_zip = os.path.join(CACHE_DIR, "electron-v37.10.3-win32-arm64.zip")
electron_url = "https://github.com/electron/electron/releases/download/v37.10.3/electron-v37.10.3-win32-arm64.zip"

if not os.path.exists(electron_zip):
    try:
        download_file(electron_url, electron_zip)
    except Exception as e:
        print(f"GitHub download failed: {e}, trying npmmirror fallback...")
        mirror_url = "https://npmmirror.com/mirrors/electron/v37.10.3/electron-v37.10.3-win32-arm64.zip"
        download_file(mirror_url, electron_zip)

print("Extracting Electron ARM64 runtime...")
with zipfile.ZipFile(electron_zip, 'r') as zip_ref:
    zip_ref.extractall(TARGET_ARM64_DIR)

# Rename electron.exe -> WorkBuddy.exe
old_exe = os.path.join(TARGET_ARM64_DIR, "electron.exe")
new_exe = os.path.join(TARGET_ARM64_DIR, "WorkBuddy.exe")
if os.path.exists(old_exe):
    os.rename(old_exe, new_exe)
    print("Renamed electron.exe to WorkBuddy.exe.")

# Embed icon.ico into WorkBuddy.exe PE header via rcedit
import subprocess, pathlib
icon_path = os.path.join(BASE_DIR, "icon.ico")
print(f"Embedding {icon_path} into WorkBuddy.exe PE header...")
new_exe_posix = pathlib.Path(new_exe).as_posix()
icon_path_posix = pathlib.Path(icon_path).as_posix()
node_cmd = f"const {{ rcedit }} = require('rcedit'); rcedit('{new_exe_posix}', {{ icon: '{icon_path_posix}' }});"
subprocess.run(['node', '-e', node_cmd], cwd=os.path.join(BASE_DIR, "build_sqlite"), check=True)
print("WorkBuddy.exe PE icon embedded successfully.")

# Copy icon.ico into target resources
shutil.copy(icon_path, os.path.join(TARGET_ARM64_DIR, "icon.ico"))


print("\n=== Step 2: Copying App Resources ===")
src_resources = os.path.join(SOURCE_APP_EXTRACTED, "resources")
dst_resources = os.path.join(TARGET_ARM64_DIR, "resources")

print(f"Copying {src_resources} -> {dst_resources} ...")
shutil.copytree(src_resources, dst_resources, dirs_exist_ok=True)
print("Resources copied successfully.")

print("\n=== Step 3: Patching better-sqlite3 win32-arm64 ===")
compiled_sqlite_node = r"c:\Developer\Personal\workbuddy-windowsarm64\build_sqlite\node_modules\better-sqlite3\build\Release\better_sqlite3.node"
with open(compiled_sqlite_node, 'rb') as f:
    extracted_node_bytes = f.read()

target_sqlite_node = os.path.join(dst_resources, r"app.asar.unpacked\node_modules\better-sqlite3\build\Release\better_sqlite3.node")
os.makedirs(os.path.dirname(target_sqlite_node), exist_ok=True)
with open(target_sqlite_node, 'wb') as f:
    f.write(extracted_node_bytes)
print(f"Patched better_sqlite3.node -> {target_sqlite_node} (ARM64)")

# Also patch bin/win32-x64-136/better-sqlite3.node if it exists
target_sqlite_bin_node = os.path.join(dst_resources, r"app.asar.unpacked\node_modules\better-sqlite3\bin\win32-x64-136\better-sqlite3.node")
if os.path.exists(os.path.dirname(target_sqlite_bin_node)):
    os.makedirs(os.path.dirname(target_sqlite_bin_node), exist_ok=True)
    with open(target_sqlite_bin_node, 'wb') as f:
        f.write(extracted_node_bytes)
    print(f"Patched better-sqlite3.node in bin directory.")

print("\n=== Step 4: Patching ripgrep (rg.exe) win32-arm64 ===")
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
    print(f"Patched rg.exe -> {target_rg} (ARM64)")

print("\n=== Step 5: Verification Scan of All PE Binaries in Output Dir ===")
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
            if machine == 0x8664:
                return 'x64'
            elif machine == 0xAA64:
                return 'ARM64'
            elif machine == 0x14C:
                return 'x86'
            else:
                return f'OTHER(0x{machine:x})'
    except Exception as e:
        return f'ERROR({e})'

binaries = []
for r, d, files in os.walk(TARGET_ARM64_DIR):
    for file in files:
        if file.endswith(('.exe', '.dll', '.node')):
            full_path = os.path.join(r, file)
            rel_path = os.path.relpath(full_path, TARGET_ARM64_DIR)
            arch = get_pe_arch(full_path)
            binaries.append((rel_path, arch))

arm64_count = sum(1 for _, arch in binaries if arch == 'ARM64')
x64_count = sum(1 for _, arch in binaries if arch == 'x64')
x86_count = sum(1 for _, arch in binaries if arch == 'x86')

print(f"Binary Audit Summary: ARM64: {arm64_count}, x64: {x64_count}, x86: {x86_count}")
print("ARM64 Binaries:")
for path, arch in sorted(binaries):
    if arch == 'ARM64':
        print(f"  [ARM64] {path}")

print("\nx64 Subprocess/Helper Binaries (Emulated seamlessly via Prism):")
for path, arch in sorted(binaries):
    if arch == 'x64':
        print(f"  [x64]   {path}")

print("\n=== BUILD AND PATCH COMPLETE ===")
