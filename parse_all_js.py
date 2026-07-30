import urllib.request
import re

base_url = "https://codebuddy-1328495429.cos.accelerate.myqcloud.com/web/workbuddy/f964788327b7a199385c77f5a9ab70ff5ad49002/assets/"
js_files = [
    "index-BGX3NU7v.js", "vendor-react-BL-3Xst8.js", "vendor-ui-D2xyfFQo.js",
    "vendor-utils-BtnIiKrK.js", "main-B0SLZ_ir.js", "index-jm8CKJwz.js",
    "vendor-animation-P_qVyXeq.js", "vendor-monitoring-aaV5mgdK.js",
    "App-DBxdVTJM.js", "personal-plans-DmMSf0fa.js"
]

for fname in js_files:
    url = base_url + fname
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            text = resp.read().decode('utf-8', errors='ignore')
            matches = re.findall(r'https?://[^\s"\'\`\>]+', text)
            for m in set(matches):
                if any(k in m.lower() for k in ['exe', 'win', 'desktop', 'download', 'release', 'package', 'setup']):
                    print(f"[{fname}] {m}")
            # Also search for API endpoints like /api/...
            api_matches = re.findall(r'/api/[a-zA-Z0-9_\-/]+', text)
            for a in set(api_matches):
                if any(k in a.lower() for k in ['download', 'app', 'version', 'latest', 'client', 'update']):
                    print(f"[{fname} API] {a}")
    except Exception as e:
        print(f"[{fname}] Error: {e}")
