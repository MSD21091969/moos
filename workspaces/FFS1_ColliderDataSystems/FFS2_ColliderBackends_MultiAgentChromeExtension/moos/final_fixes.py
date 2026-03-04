import re
path = 'internal/session/manager.go'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix `_ = \n`
text = re.sub(r'_\s*=\s*\}', '}', text)
text = re.sub(r'_\s*=\s*\n', '\n', text)
text = re.sub(r'_\s*=\s*continue', 'continue', text)

# Fix manager.store usages
text = re.sub(r'_\s*=\s*manager\.store\.Delete\(.*?\)\n', '\n', text)
text = re.sub(r'manager\.store\.Get\(.*?\)\n', '\n', text)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
