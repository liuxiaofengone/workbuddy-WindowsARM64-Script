import os
import re

app_dir = r'c:\Developer\Personal\workbuddy-windowsarm64\app_extracted'
found = set()
for r, d, files in os.walk(app_dir):
    for f in files:
        if f.endswith(('.js', '.json')):
            fp = os.path.join(r, f)
            try:
                with open(fp, 'r', encoding='utf-8', errors='ignore') as file:
                    txt = file.read()
                    matches = re.findall(r'https?://[^\s"\'\`\>]+', txt)
                    for m in matches:
                        if any(k in m.lower() for k in ['download', 'update', 'latest', 'release', 'cos', 'workbuddy']):
                            found.add(m)
            except Exception:
                pass

for u in sorted(found):
    print(u)
