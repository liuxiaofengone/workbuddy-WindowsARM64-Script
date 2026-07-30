import urllib.request
import re

urls = [
    "https://download.codebuddy.cn/web/workbuddy/0bebf86e38e7d71ff0c313d661e7753ff996c54e/assets/App-CsPcTC3R.js",
    "https://download.codebuddy.cn/web/workbuddy/0bebf86e38e7d71ff0c313d661e7753ff996c54e/assets/vendor-utils-fR7rg6A1.js"
]

for url in urls:
    r = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(r) as resp:
        text = resp.read().decode('utf-8', errors='ignore')
    for m in re.finditer(r'dr\s*=\s*|axios\.create', text):
        start = max(0, m.start() - 100)
        end = min(len(text), m.end() + 200)
        print("=== AXIOS/DR CONTEXT ===")
        print(text[start:end])
