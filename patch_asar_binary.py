import os
import sys

def patch_app_asar(app_asar_path: str):
    print(f"[*] Inspecting app.asar for patching: {app_asar_path}")
    if not os.path.exists(app_asar_path):
        print(f"[!] Error: app.asar not found at {app_asar_path}")
        return False
        
    with open(app_asar_path, 'rb') as f:
        content = f.read()
        
    target_pattern = (
        'case MENU_COMMAND_IDS.CHECK_FOR_UPDATES:\n'
        '\t\tcase MENU_COMMAND_IDS.DOWNLOAD_UPDATE:\n'
        '\t\t\tawait (await deps.update).check(true);\n'
        '\t\t\treturn;\n'
        '\t\tcase MENU_COMMAND_IDS.INSTALL_UPDATE:\n'
        '\t\t\tawait (await deps.update).quitAndInstall();\n'
        '\t\t\treturn;'
    ).encode('utf-8')
    
    target_idx = content.find(target_pattern)
    if target_idx == -1:
        print("[!] Target update pattern not found in app.asar (may already be patched).")
        return False
        
    target_len = len(target_pattern)
    print(f"[+] Found target update pattern at offset {target_idx}, target length: {target_len} bytes.")
    
    # Custom JS handler logic for ARM64 update check
    custom_js = (
        'case MENU_COMMAND_IDS.CHECK_FOR_UPDATES:case MENU_COMMAND_IDS.DOWNLOAD_UPDATE:case MENU_COMMAND_IDS.INSTALL_UPDATE:{'
        '(async()=>{try{const{dialog:d,shell:s}=require("electron"),cp=require("child_process"),p=require("path"),fs=require("fs"),'
        'h=require("https"),v=deps.app?deps.app.getVersion():"5.3.8";'
        'h.get("https://www.workbuddy.cn/v2/update?platform=workbuddy-win32-x64-user",{headers:{"User-Agent":"Mozilla/5.0"}},r=>'
        '{let b="";r.on("data",c=>b+=c);r.on("end",()=>{try{const data=JSON.parse(b),ov=data.version||"";'
        'if(ov&&ov!==v){const btn=d.showMessageBoxSync({type:"info",buttons:["立即启动原生 ARM64 一键升级引擎","稍后提醒"],'
        'defaultId:0,title:"WorkBuddy ARM64 发现新版本",message:`检测到官方最新版本 v${ov} (当前 v${v})。`,'
        'detail:"点击确认将自动启动 ARM64 原生下载重编译与打包升级程序！"});'
        'if(btn===0){const u=p.join(process.resourcesPath,"..","tools","arm64_updater","build.bat");'
        'if(fs.existsSync(u)){cp.spawn("cmd.exe",["/c","start","cmd.exe","/k",u],{detached:true,stdio:"ignore"})}'
        'else{s.openExternal("https://github.com/liuxiaofengone/workbuddy-WindowsARM64-Script")}}}'
        'else{d.showMessageBoxSync({type:"info",buttons:["确定"],title:"检查更新",message:`当前 WorkBuddy (v${v}) 已是最新版本！`})}'
        '}catch(e){d.showErrorBox("检查更新失败",String(e))}}).on("error",e=>d.showErrorBox("网络失败",String(e)))'
        '}catch(e){}})();return;}'
    )
    
    code_bytes = custom_js.encode('utf-8')
    code_len = len(code_bytes)
    
    if code_len > target_len:
        print(f"[!] ERROR: Custom JS ({code_len} bytes) is longer than target ({target_len} bytes)!")
        return False
        
    pad_needed = target_len - code_len
    if pad_needed > 0:
        if pad_needed < 4:
            # Pad spaces if comment overhead is too small
            padding = b' ' * pad_needed
        else:
            # Use JS block comment /* **** */
            padding = b'/*' + (b'*' * (pad_needed - 4)) + b'*/'
        final_replacement = code_bytes + padding
    else:
        final_replacement = code_bytes
        
    assert len(final_replacement) == target_len, f"Length mismatch: {len(final_replacement)} != {target_len}"
    
    new_content = content[:target_idx] + final_replacement + content[target_idx + target_len:]
    with open(app_asar_path, 'wb') as f:
        f.write(new_content)
        
    print(f"[+] Successfully patched app.asar! Byte length preserved: {len(content)} bytes.")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        patch_app_asar(sys.argv[1])
