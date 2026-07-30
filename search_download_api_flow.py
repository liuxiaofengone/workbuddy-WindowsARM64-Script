import urllib.request
import re

url = "https://download.codebuddy.cn/web/workbuddy/0bebf86e38e7d71ff0c313d661e7753ff996c54e/assets/App-CsPcTC3R.js"
r = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(r) as resp:
    text = resp.read().decode('utf-8', errors='ignore')

idx = text.find('workbuddy-win32-x64-user')
if idx != -1:
    start = max(0, idx - 400)
    end = min(len(text), idx + 400)
    print("=== API Flow Snippet ===")
    print(text[start:end])
