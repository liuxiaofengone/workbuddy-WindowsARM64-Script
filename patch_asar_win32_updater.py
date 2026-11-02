import os
import sys
import re

def patch_app_asar_win32_updater(app_asar_path: str) -> bool:
    print(f"[*] Inspecting app.asar for Direct Connection (直连) ARM64 Win32 Update Service and Storage Bootstrap patches: {app_asar_path}")
    if not os.path.exists(app_asar_path):
        print(f"[!] Error: app.asar not found at {app_asar_path}")
        return False
        
    with open(app_asar_path, 'rb') as f:
        content = f.read()
        
    orig_len = len(content)
    new_content = content
    storage_success = False
    updater_success = False

    # 1. Patch storage bootstrap failure check to prevent "Workbuddy 关键组件加载失败" popup
    m_storage = re.search(rb'function\s+isStorageBootstrapLoggerGetFailed\s*\(\)\s*\{\s*return\s+loggerGetFailed\s*\}', new_content)
    if m_storage:
        s_start = m_storage.start()
        s_end = m_storage.end()
        s_len = s_end - s_start
        rep = b'function isStorageBootstrapLoggerGetFailed(){return!1;}'
        if len(rep) <= s_len:
            pad = s_len - len(rep)
            if pad >= 4:
                rep_block = b'function isStorageBootstrapLoggerGetFailed(){return!1;/*' + (b'*' * (pad - 4)) + b'*/}'
            else:
                rep_block = b'function isStorageBootstrapLoggerGetFailed(){return!1;}' + (b' ' * pad)
            assert len(rep_block) == s_len, f"Storage block len mismatch: {len(rep_block)} != {s_len}"
            new_content = new_content[:s_start] + rep_block + new_content[s_end:]
            print(f"[+] Successfully patched isStorageBootstrapLoggerGetFailed at offset {s_start} to prevent false positive warning dialog!")
            storage_success = True
    else:
        if b'function isStorageBootstrapLoggerGetFailed(){return!1;' in new_content:
            print("[+] isStorageBootstrapLoggerGetFailed is already patched (returns !1).")
            storage_success = True
        else:
            print("[!] Warning: isStorageBootstrapLoggerGetFailed pattern not found in app.asar!")

    # 2. Patch Win32 UpdateService for Direct Connection (直连)
    idx_win32 = new_content.find(b'[UpdateService.win32]')
    if idx_win32 == -1:
        print("[!] [UpdateService.win32] marker not found in app.asar")
    else:
        # Search in a bidirectional window around [UpdateService.win32] (async checkForUpdates can appear slightly before or after)
        window_start = max(0, idx_win32 - 15000)
        window_end = min(len(new_content), idx_win32 + 25000)
        matches = list(re.finditer(rb'async\s+checkForUpdates\s*\([^\)]*\)\s*\{', new_content[window_start:window_end]))
        if not matches:
            print("[!] checkForUpdates start pattern not found near Win32 UpdateService")
        else:
            # Pick the match closest to idx_win32
            best_match = min(matches, key=lambda m: abs((window_start + m.start()) - idx_win32))
            idx_start = window_start + best_match.start()
            m_dl = re.search(rb'async\s+downloadUpdate\s*\([^\)]*\)\s*\{', new_content[idx_start:idx_start+20000])
            if not m_dl:
                print("[!] downloadUpdate pattern not found after Win32 checkForUpdates")
            else:
                idx_end = idx_start + m_dl.start()
                target_block = new_content[idx_start:idx_end]
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
                    '\t\t\tconst _path = require("path");\n'
                    '\t\t\tconst _fs = require("fs");\n'
                    '\t\t\tconst _el = typeof electron !== "undefined" ? electron : require("electron");\n'
                    '\t\t\tconst req = h.get(feedUrl, { headers: { "User-Agent": "Mozilla/5.0" } }, (res) => {\n'
                    '\t\t\t\tlet body = "";\n'
                    '\t\t\t\tres.on("data", c => body += c);\n'
                    '\t\t\t\tres.on("end", () => {\n'
                    '\t\t\t\t\ttry {\n'
                    '\t\t\t\t\t\tconst data = JSON.parse(body);\n'
                    '\t\t\t\t\t\tconst onlineVer = data.version || data.productVersion || "";\n'
                    '\t\t\t\t\t\tif (onlineVer && this.isNewVersion(onlineVer, curVer)) {\n'
                    '\t\t\t\t\t\t\tconst btn = _el.dialog.showMessageBoxSync({\n'
                    '\t\t\t\t\t\t\t\ttype: "info",\n'
                    '\t\t\t\t\t\t\t\tbuttons: ["立即启动原生 ARM64 一键升级引擎", "稍后提醒"],\n'
                    '\t\t\t\t\t\t\t\tdefaultId: 0,\n'
                    '\t\t\t\t\t\t\t\ttitle: "WorkBuddy ARM64 发现新版本更新",\n'
                    '\t\t\t\t\t\t\t\tmessage: `检测到官方最新版本 v${onlineVer} (当前已安装 v${curVer})。`,\n'
                    '\t\t\t\t\t\t\t\tdetail: "点击“确认”将自动启动 ARM64 原生下载重编译与打包升级程序！"\n'
                    '\t\t\t\t\t\t\t});\n'
                    '\t\t\t\t\t\t\tif (btn === 0) {\n'
                    '\t\t\t\t\t\t\t\tconst toolsDir = _path.join(process.resourcesPath, "..", "tools", "arm64_updater");\n'
                    '\t\t\t\t\t\t\t\tconst updaterBat = _path.join(toolsDir, "build.bat");\n'
                    '\t\t\t\t\t\t\t\tif (_fs.existsSync(updaterBat)) {\n'
                    '\t\t\t\t\t\t\t\t\trequire("child_process").spawn("cmd.exe", ["/c", "start", "cmd.exe", "/k", updaterBat], { detached: true, stdio: "ignore" });\n'
                    '\t\t\t\t\t\t\t\t} else {\n'
                    '\t\t\t\t\t\t\t\t\t_el.shell.openExternal("https://github.com/liuxiaofengone/workbuddy-WindowsARM64-Script");\n'
                    '\t\t\t\t\t\t\t\t}\n'
                    '\t\t\t\t\t\t\t}\n'
                    '\t\t\t\t\t\t} else if (explicit) {\n'
                    '\t\t\t\t\t\t\t_el.dialog.showMessageBoxSync({\n'
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
                    '\t\t\t\t\t_el.dialog.showMessageBoxSync({\n'
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
                else:
                    pad_needed = target_len - code_len
                    if pad_needed >= 4:
                        padding = b'/*' + (b'*' * (pad_needed - 4)) + b'*/'
                    else:
                        padding = b' ' * pad_needed
                    final_block = code_bytes + padding
                    assert len(final_block) == target_len, f"Len mismatch: {len(final_block)} != {target_len}"
                    new_content = new_content[:idx_start] + final_block + new_content[idx_end:]
                    print(f"[+] Successfully patched Win32 checkForUpdates for Direct Connection (直连)!")
                    updater_success = True

    assert len(new_content) == orig_len, f"ASAR size changed: {len(new_content)} != {orig_len}"

    if storage_success or updater_success:
        with open(app_asar_path, 'wb') as f:
            f.write(new_content)
        print(f"[+] Successfully wrote patched app.asar! Size preserved: {len(new_content)} bytes.")
        return True
    else:
        print("[!] No patches were applied to app.asar.")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        patch_app_asar_win32_updater(sys.argv[1])
