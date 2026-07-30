import urllib.request
import re

urls = [
    "https://codebuddy-1328495429.cos.accelerate.myqcloud.com/web/workbuddy/f964788327b7a199385c77f5a9ab70ff5ad49002/assets/main-B0SLZ_ir.js",
    "https://codebuddy-1328495429.cos.accelerate.myqcloud.com/web/workbuddy/f964788327b7a199385c77f5a9ab70ff5ad49002/assets/index-BGX3NU7v.js"
]

for url in urls:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        text = resp.read().decode('utf-8')
    print("Searching:", url)
    print("Found .exe occurrences:")
    for m in re.finditer(r'.{0,50}\.exe.{0,50}', text):
        print("  ", m.group(0))
    print("Found client/update/download API occurrences:")
    for m in re.finditer(r'.{0,30}(?:download|latest|version|release|client).{0,30}', text, re.IGNORECASE):
        sub = m.group(0)
        if any(w in sub for w in ['http', 'api', 'cos', 'url', 'win']):
            print("  ", sub)
