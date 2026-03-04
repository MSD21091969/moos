import os

path = 'internal/session/manager.go'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

target = "go manager.runSession(state)\n\t}\n}"

idx = text.find(target)
if idx != -1:
    clean_text = text[:idx + len(target)] + "\n"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(clean_text)
    print("truncated extra stuff at end")
