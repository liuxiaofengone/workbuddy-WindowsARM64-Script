import urllib.request
import re

url = "https://www.workbuddy.cn/"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8')

js_urls = re.findall(r'src=["\']([^"\']+\.js)["\']', html)
preloads = re.findall(r'href=["\']([^"\']+\.js)["\']', html)

all_js = set(js_urls + preloads)
print("Found CN JS links:", all_js)

for js in all_js:
    if js.startswith("//"):
        js = "https:" + js
    try:
        r = urllib.request.Request(js, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(r) as resp:
            text = resp.read().decode('utf-8', errors='ignore')
            for m in re.finditer(r'https?://[^\s"\'\`\>]+', text):
                u = m.group(0)
                if any(ext in u.lower() for ext in ['exe', 'win', 'download', 'release', 'desktop']):
                    print("LINK:", u)
    except Exception as e:
        print("Error reading", js, e)
