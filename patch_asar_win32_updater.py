import os
import sys

def patch_app_asar_win32_updater(app_asar_path: str) -> bool:
    print(f"[*] Inspecting app.asar for ARM64 Win32 Update Service patch: {app_asar_path}")
    if not os.path.exists(app_asar_path):
        print(f"[!] Error: app.asar not found at {app_asar_path}")
        return False
        
    with open(app_asar_path, 'rb') as f:
        content = f.read()
        
    # Patch 1: Show "Up to date" dialog on explicit check if no new version
    pattern_idle = (
        'this.logger?.info(`[UpdateService.win32] No new version available (remote: ${updateInfo.productVersion}, current: ${this.version})`);\n'
        '\t\t\t\tthis.fileLogger.info(`[win32] No new version available (remote: ${updateInfo.productVersion}, current: ${this.version})`);\n'
        '\t\t\t\tthis.setState("idle");'
    ).encode('utf-8')
    
    idx_idle = content.find(pattern_idle)
    if idx_idle != -1:
        replacement_idle = (
            'this.logger?.info(`[UpdateService.win32] No new version available (remote: ${updateInfo.productVersion}, current: ${this.version})`);\n'
            '\t\t\t\tthis.fileLogger.info(`[win32] No new version available (remote: ${updateInfo.productVersion}, current: ${this.version})`);\n'
            '\t\t\t\tif(this.lastExplicit){electron.dialog.showMessageBoxSync({type:"info",buttons:["确定"],title:"检查更新",message:`当前 WorkBuddy (v${this.version}) 已是最新版本！`});}\n'
            '\t\t\t\tthis.setState("idle");'
        ).encode('utf-8')
        
        # Calculate padding needed or adjust
        len_orig = len(pattern_idle)
        len_new = len(replacement_idle)
        print(f"[+] Idle pattern found, orig len: {len_orig}, new len: {len_new}")
        
    # Patch 2: Intercept downloadUpdate to launch ARM64 build.bat
    pattern_dl = (
        'async downloadUpdate(updateInfo) {\n'
        '\t\tconst targetVersion = updateInfo.productVersion;'
    ).encode('utf-8')
    
    idx_dl = content.find(pattern_dl)
    if idx_dl == -1:
        print("[!] downloadUpdate pattern not found in app.asar")
        return False
        
    # Find the end of downloadUpdate method
    pattern_dl_end = 'code: "DOWNLOAD_ERROR"\n\t\t\t\t});\n\t\t\t}\n\t\t}\n\t}'.encode('utf-8')
    idx_dl_end = content.find(pattern_dl_end, idx_dl)
    if idx_dl_end == -1:
        print("[!] End of downloadUpdate method not found")
        return False
        
    target_len = (idx_dl_end + len(pattern_dl_end)) - idx_dl
    target_block = content[idx_dl : idx_dl + target_len]
    print(f"[+] Found downloadUpdate block at offset {idx_dl}, size: {target_len} bytes.")
    
    new_dl_code = (
        'async downloadUpdate(updateInfo) {\n'
        '\t\tconst targetVersion = updateInfo.productVersion;\n'
        '\t\ttry {\n'
        '\t\t\tconst curVer = this.version || "5.3.8";\n'
        '\t\t\tconst btn = electron.dialog.showMessageBoxSync({\n'
        '\t\t\t\ttype: "info",\n'
        '\t\t\t\tbuttons: ["立即启动原生 ARM64 一键升级引擎", "稍后提醒"],\n'
        '\t\t\t\tdefaultId: 0,\n'
        '\t\t\t\ttitle: "WorkBuddy ARM64 发现新版本更新",\n'
        '\t\t\t\tmessage: `检测到官方最新版本 v${targetVersion} (当前已安装 v${curVer})。`,\n'
        '\t\t\t\tdetail: "点击确认将自动启动 ARM64 原生下载重编译与打包升级程序！"\n'
        '\t\t\t});\n'
        '\t\t\tif (btn === 0) {\n'
        '\t\t\t\tconst toolsDir = path.join(process.resourcesPath, "..", "tools", "arm64_updater");\n'
        '\t\t\t\tconst updaterBat = path.join(toolsDir, "build.bat");\n'
        '\t\t\t\tif (fs.existsSync(updaterBat)) {\n'
        '\t\t\t\t\trequire("child_process").spawn("cmd.exe", ["/c", "start", "cmd.exe", "/k", updaterBat], { detached: true, stdio: "ignore" });\n'
        '\t\t\t\t} else {\n'
        '\t\t\t\t\telectron.shell.openExternal("https://github.com/liuxiaofengone/workbuddy-WindowsARM64-Script");\n'
        '\t\t\t\t}\n'
        '\t\t\t}\n'
        '\t\t\tthis.setState("idle");\n'
        '\t\t} catch(e) {\n'
        '\t\t\tthis.setState("idle");\n'
        '\t\t}\n'
        '\t}'
    ).encode('utf-8')
    
    new_dl_len = len(new_dl_code)
    if new_dl_len > target_len:
        print(f"[!] ERROR: New downloadUpdate code ({new_dl_len} bytes) exceeds target ({target_len} bytes)!")
        return False
        
    pad_needed = target_len - new_dl_len
    if pad_needed >= 4:
        comment = b'\n\t/*' + (b'*' * (pad_needed - 6)) + b'*/'
        final_dl_block = new_dl_code + comment
    else:
        final_dl_block = new_dl_code + (b' ' * pad_needed)
        
    assert len(final_dl_block) == target_len, f"Len mismatch: {len(final_dl_block)} != {target_len}"
    
    new_content = content[:idx_dl] + final_dl_block + content[idx_dl + target_len:]
    
    with open(app_asar_path, 'wb') as f:
        f.write(new_content)
        
    print(f"[+] Successfully patched app.asar for ARM64 Win32 Update Service! Size preserved: {len(new_content)} bytes.")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        patch_app_asar_win32_updater(sys.argv[1])
