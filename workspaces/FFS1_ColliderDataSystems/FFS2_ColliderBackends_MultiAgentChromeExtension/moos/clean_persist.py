import re

path = 'internal/session/manager.go'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'func \(manager \*Manager\) persistState\(state \*sessionState\) \{.*?\}\n', '', text, flags=re.DOTALL)
text = text.replace("manager.persistState(state)\n", "")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
