import urllib.request
import re

url = "https://www.workbuddy.ai/"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8')
    js_urls = re.findall(r'src=["\']([^"\']+\.js)["\']', html)
    print("Found JS files:", js_urls)
    for js_url in js_urls:
        if js_url.startswith("//"):
            js_url = "https:" + js_url
        req_js = urllib.request.Request(js_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_js) as r_js:
            content = r_js.read().decode('utf-8', errors='ignore')
            matches = re.findall(r'https?://[^\s"\'\`\>]+', content)
            for m in set(matches):
                if any(k in m.lower() for k in ['download', 'workbuddy', 'exe', 'win', 'desktop', 'latest']):
                    print(m)
except Exception as e:
    print("Error:", e)
