import os
import sys

def patch_app_asar_win32_updater(app_asar_path: str) -> bool:
    print(f"[*] Inspecting app.asar for Direct Connection (直连) ARM64 Win32 Update Service patch: {app_asar_path}")
    if not os.path.exists(app_asar_path):
        print(f"[!] Error: app.asar not found at {app_asar_path}")
        return False
        
    with open(app_asar_path, 'rb') as f:
        content = f.read()
        
    idx_win32 = content.find(b'[UpdateService.win32]')
    if idx_win32 == -1:
        print("[!] [UpdateService.win32] marker not found in app.asar")
        return False
        
    pattern_start = b'async checkForUpdates(explicit = false) {'
    idx_start = content.find(pattern_start, idx_win32)
    if idx_start == -1:
        print("[!] checkForUpdates start pattern not found in Win32 UpdateService")
        return False
        
    pattern_end = b'async downloadUpdate(updateInfo) {'
    idx_end = content.find(pattern_end, idx_start)
    if idx_end == -1:
        print("[!] downloadUpdate pattern not found after Win32 checkForUpdates")
        return False
        
    target_block = content[idx_start:idx_end]
    target_len = len(target_block)
    print(f"[+] Found Win32 checkForUpdates block at offset {idx_start}, total block size: {target_len} bytes.")
    
    # Custom JS handler logic: Node native https.get for 100% DIRECT CONNECTION (直连), bypassing proxy errors & ugly toasts!
    custom_js = (
        'async checkForUpdates(explicit = false) {\n'
        '\t\tif (this.checkInProgress) return;\n'
        '\t\tthis.checkInProgress = true;\n'
        '\t\ttry {\n'
        '\t\t\tthis.setState("checking");\n'
        '\t\t\tconst curVer = this.version || "5.3.8";\n'
        '\t\t\tconst feedUrl = "https://www.workbuddy.cn/v2/update?platform=workbuddy-win32-x64-user";\n'
        '\t\t\tconst h = require("https");\n'
        '\t\t\tconst req = h.get(feedUrl, { headers: { "User-Agent": "Mozilla/5.0" } }, (res) => {\n'
        '\t\t\t\tlet body = "";\n'
        '\t\t\t\tres.on("data", c => body += c);\n'
        '\t\t\t\tres.on("end", () => {\n'
        '\t\t\t\t\ttry {\n'
        '\t\t\t\t\t\tconst data = JSON.parse(body);\n'
        '\t\t\t\t\t\tconst onlineVer = data.version || data.productVersion || "";\n'
        '\t\t\t\t\t\tif (onlineVer && this.isNewVersion(onlineVer, curVer)) {\n'
        '\t\t\t\t\t\t\tconst btn = electron.dialog.showMessageBoxSync({\n'
        '\t\t\t\t\t\t\t\ttype: "info",\n'
        '\t\t\t\t\t\t\t\tbuttons: ["立即启动原生 ARM64 一键升级引擎", "稍后提醒"],\n'
        '\t\t\t\t\t\t\t\tdefaultId: 0,\n'
        '\t\t\t\t\t\t\t\ttitle: "WorkBuddy ARM64 发现新版本更新",\n'
        '\t\t\t\t\t\t\t\tmessage: `检测到官方最新版本 v${onlineVer} (当前已安装 v${curVer})。`,\n'
        '\t\t\t\t\t\t\t\tdetail: "点击“确认”将自动启动 ARM64 原生下载重编译与打包升级程序！"\n'
        '\t\t\t\t\t\t\t});\n'
        '\t\t\t\t\t\t\tif (btn === 0) {\n'
        '\t\t\t\t\t\t\t\tconst toolsDir = path.join(process.resourcesPath, "..", "tools", "arm64_updater");\n'
        '\t\t\t\t\t\t\t\tconst updaterBat = path.join(toolsDir, "build.bat");\n'
        '\t\t\t\t\t\t\t\tif (fs.existsSync(updaterBat)) {\n'
        '\t\t\t\t\t\t\t\t\trequire("child_process").spawn("cmd.exe", ["/c", "start", "cmd.exe", "/k", updaterBat], { detached: true, stdio: "ignore" });\n'
        '\t\t\t\t\t\t\t\t} else {\n'
        '\t\t\t\t\t\t\t\t\telectron.shell.openExternal("https://github.com/liuxiaofengone/workbuddy-WindowsARM64-Script");\n'
        '\t\t\t\t\t\t\t\t}\n'
        '\t\t\t\t\t\t\t}\n'
        '\t\t\t\t\t\t} else if (explicit) {\n'
        '\t\t\t\t\t\t\telectron.dialog.showMessageBoxSync({\n'
        '\t\t\t\t\t\t\t\ttype: "info",\n'
        '\t\t\t\t\t\t\t\tbuttons: ["确定"],\n'
        '\t\t\t\t\t\t\t\ttitle: "检查更新",\n'
        '\t\t\t\t\t\t\t\tmessage: `当前 WorkBuddy (v${curVer}) 已是最新版本！`\n'
        '\t\t\t\t\t\t\t});\n'
        '\t\t\t\t\t\t}\n'
        '\t\t\t\t\t} catch(e) {}\n'
        '\t\t\t\t\tthis.setState("idle");\n'
        '\t\t\t\t});\n'
        '\t\t\t});\n'
        '\t\t\treq.on("error", () => {\n'
        '\t\t\t\tif (explicit) {\n'
        '\t\t\t\t\telectron.dialog.showMessageBoxSync({\n'
        '\t\t\t\t\t\ttype: "warning",\n'
        '\t\t\t\t\t\tbuttons: ["确定"],\n'
        '\t\t\t\t\t\ttitle: "检查更新",\n'
        '\t\t\t\t\t\tmessage: "无法连接官方更新服务器，请检查网络连接。"\n'
        '\t\t\t\t\t});\n'
        '\t\t\t\t}\n'
        '\t\t\t\tthis.setState("idle");\n'
        '\t\t\t});\n'
        '\t\t\treq.setTimeout(8000, () => {\n'
        '\t\t\t\treq.destroy();\n'
        '\t\t\t\tthis.setState("idle");\n'
        '\t\t\t});\n'
        '\t\t} catch(e) {\n'
        '\t\t\tthis.setState("idle");\n'
        '\t\t} finally {\n'
        '\t\t\tthis.checkInProgress = false;\n'
        '\t\t}\n'
        '\t}\n'
    )
    
    code_bytes = custom_js.encode('utf-8')
    code_len = len(code_bytes)
    
    if code_len > target_len:
        print(f"[!] ERROR: Custom JS ({code_len} bytes) exceeds target block ({target_len} bytes)!")
        return False
        
    pad_needed = target_len - code_len
    if pad_needed >= 4:
        padding = b'/*' + (b'*' * (pad_needed - 4)) + b'*/'
    else:
        padding = b' ' * pad_needed
        
    final_block = code_bytes + padding
    assert len(final_block) == target_len, f"Len mismatch: {len(final_block)} != {target_len}"
    
    new_content = content[:idx_start] + final_block + content[idx_end:]
    
    with open(app_asar_path, 'wb') as f:
        f.write(new_content)
        
    print(f"[+] Successfully patched app.asar for Direct Connection (直连) Update Check! Size preserved: {len(new_content)} bytes.")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        patch_app_asar_win32_updater(sys.argv[1])
