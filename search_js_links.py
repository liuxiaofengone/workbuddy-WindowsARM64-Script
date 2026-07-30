import urllib.request
import re

url = "https://codebuddy-1328495429.cos.accelerate.myqcloud.com/web/workbuddy/f964788327b7a199385c77f5a9ab70ff5ad49002/assets/App-DBxdVTJM.js"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    text = resp.read().decode('utf-8')

# Search for strings containing cos.accelerate, myqcloud, codebuddy, or download
matches = re.findall(r'["\'](https?:[^"\']+)["\']', text)
for m in set(matches):
    if any(k in m for k in ['codebuddy', 'workbuddy', 'download', 'cos', 'myqcloud']):
        print(m)
