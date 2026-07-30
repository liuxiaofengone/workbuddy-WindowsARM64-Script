import urllib.request
import re

url = "https://codebuddy-1328495429.cos.accelerate.myqcloud.com/web/workbuddy/f964788327b7a199385c77f5a9ab70ff5ad49002/assets/App-DBxdVTJM.js"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    text = resp.read().decode('utf-8')

# Search for window.location.href or window.open or a.href assignment
matches = re.finditer(r'(?:href|location|open|download)\s*[:=]\s*[`"\']([^`"\']+)[`"\']', text)
for m in matches:
    val = m.group(1)
    if 'http' in val or 'codebuddy' in val or 'workbuddy' in val or 'download' in val:
        print(val)
