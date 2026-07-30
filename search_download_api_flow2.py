import urllib.request
import re

url = "https://download.codebuddy.cn/web/workbuddy/0bebf86e38e7d71ff0c313d661e7753ff996c54e/assets/App-CsPcTC3R.js"
r = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(r) as resp:
    text = resp.read().decode('utf-8', errors='ignore')

for m in re.finditer(r'jr\.workbuddy|\.replace\("\.zip",\s*"\.exe"\)', text):
    start = max(0, m.start() - 300)
    end = min(len(text), m.end() + 300)
    print("=== SNIPPET ===")
    print(text[start:end])
