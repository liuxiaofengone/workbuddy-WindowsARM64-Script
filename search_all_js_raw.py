import urllib.request
import re

urls = [
    "https://codebuddy-1328495429.cos.accelerate.myqcloud.com/web/workbuddy/f964788327b7a199385c77f5a9ab70ff5ad49002/assets/App-DBxdVTJM.js",
    "https://codebuddy-1328495429.cos.accelerate.myqcloud.com/web/workbuddy/f964788327b7a199385c77f5a9ab70ff5ad49002/assets/main-B0SLZ_ir.js",
    "https://codebuddy-1328495429.cos.accelerate.myqcloud.com/web/workbuddy/f964788327b7a199385c77f5a9ab70ff5ad49002/assets/index-BGX3NU7v.js"
]

for url in urls:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        text = resp.read().decode('utf-8')
    for m in re.finditer(r'["\'](https?://download\.codebuddy\.cn/[^"\']+)["\']', text):
        print("LINK:", m.group(1))
    for m in re.finditer(r'["\'](https?://[^"\']+\.(?:exe|zip|dmg|json))["\']', text):
        print("FILE:", m.group(1))
