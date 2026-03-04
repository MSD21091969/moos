import os
import re

path = r"internal/session/manager.go"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("_ =\n", "")
text = text.replace("_\n\t\t\t\t=", "")
text = text.replace("_\n\t\t=", "")
text = re.sub(r"_\s*=\s*\n", "\n", text)
with open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("cleaned up blank assignments")
