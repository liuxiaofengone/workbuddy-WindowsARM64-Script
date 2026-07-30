import urllib.request
import re

sites = ['https://www.codebuddy.cn/', 'https://www.workbuddy.cn/']
for site in sites:
    try:
        req = urllib.request.Request(site, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            print(site, 'HTML len:', len(html))
            urls = re.findall(r'https?://[^\s"\'\`\>]+', html)
            for u in set(urls):
                if any(ext in u.lower() for ext in ['exe', 'download', 'win']):
                    print('  ', u)
    except Exception as e:
        print(site, 'Error:', e)
