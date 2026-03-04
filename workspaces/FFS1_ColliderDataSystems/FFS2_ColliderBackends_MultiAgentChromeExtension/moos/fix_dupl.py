import os

path = r"internal/session/manager.go"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

parts = text.split("func (manager *Manager) appendMessage")
if len(parts) > 2:
    # keeps only the first one
    good_text = parts[0] + "func (manager *Manager) appendMessage" + parts[1]
    with open(path, "w", encoding="utf-8") as f:
        f.write(good_text)
    print("removed duplicate appendMessage")
