import urllib.request
import re

js_list = [
    'https://download.codebuddy.cn/web/workbuddy/0bebf86e38e7d71ff0c313d661e7753ff996c54e/assets/main-C-zNNITX.js',
    'https://download.codebuddy.cn/web/workbuddy/0bebf86e38e7d71ff0c313d661e7753ff996c54e/assets/App-CsPcTC3R.js',
    'https://download.codebuddy.cn/web/workbuddy/0bebf86e38e7d71ff0c313d661e7753ff996c54e/assets/index-D8vktNyC.js',
    'https://download.codebuddy.cn/web/workbuddy/0bebf86e38e7d71ff0c313d661e7753ff996c54e/assets/vendor-ui-_FW-tKsw.js'
]

for url in js_list:
    r = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(r) as resp:
        text = resp.read().decode('utf-8', errors='ignore')
    print("Searching", url)
    for m in re.finditer(r'.{0,40}(?:WorkBuddy|codebuddy|download|win32|\.exe).{0,40}', text, re.IGNORECASE):
        sub = m.group(0)
        if any(k in sub for k in ['http', 'api', 'cos', 'url', 'exe', 'user']):
            print("  MATCH:", sub.encode('ascii', errors='ignore').decode('ascii'))
