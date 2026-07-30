import urllib.request
import re

url = 'https://download.codebuddy.cn/web/workbuddy/0bebf86e38e7d71ff0c313d661e7753ff996c54e/assets/vendor-utils-fR7rg6A1.js'
r = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(r) as resp:
    text = resp.read().decode('utf-8', errors='ignore')

for m in re.finditer(r'https?://[^\s"\'\`\>]+', text):
    print(m.group(0))

for m in re.finditer(r'["\'](/v[12]/[^"\']+)["\']', text):
    print("ROUTE:", m.group(1))
