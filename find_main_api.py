import urllib.request
import re

url = "https://download.codebuddy.cn/web/workbuddy/0bebf86e38e7d71ff0c313d661e7753ff996c54e/assets/main-C-zNNITX.js"
r = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(r) as resp:
    text = resp.read().decode('utf-8', errors='ignore')

for m in re.finditer(r'https?://[^\s"\'\`\>]+', text):
    u = m.group(0)
    if 'codebuddy' in u or 'workbuddy' in u or 'tencent' in u or 'api' in u:
        print(u)
