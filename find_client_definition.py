import urllib.request
import re

url = "https://download.codebuddy.cn/web/workbuddy/0bebf86e38e7d71ff0c313d661e7753ff996c54e/assets/App-CsPcTC3R.js"
r = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(r) as resp:
    text = resp.read().decode('utf-8', errors='ignore')

m = re.search(r'const _t\s*=\s*r\s*=>\s*([a-zA-Z0-9_$]+)\.get\(', text)
if m:
    client_var = m.group(1)
    print("Client var name:", client_var)
    # search where client_var is defined
    for m2 in re.finditer(rf'{client_var}\s*=\s*([^;,]+)', text):
        print("Definition:", m2.group(0))
