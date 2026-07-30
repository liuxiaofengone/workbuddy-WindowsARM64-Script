import re

with open(r'C:\Users\liuxi\.gemini\antigravity\brain\6c718db0-48df-47e2-a190-5f1d0fc34fc0\.system_generated\steps\539\content.md', 'r', encoding='utf-8') as f:
    text = f.read()

urls = re.findall(r'https?://[^\s\"\'\>]+', text)
for u in set(urls):
    if any(ext in u.lower() for ext in ['exe', 'zip', 'dmg', 'api', 'download', 'latest', 'release', 'update', 'version']):
        print(u)
