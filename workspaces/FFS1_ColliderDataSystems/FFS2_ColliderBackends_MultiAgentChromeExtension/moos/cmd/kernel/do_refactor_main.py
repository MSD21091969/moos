import os
import re

path = r"D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\moos\cmd\kernel\main.go"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

text = re.sub(
    r"sessionStore, storeErr := session\.NewStoreWithFallback\(.*?\n\s+if storeErr != nil \{\n\s+logger\.Warn\(\"session store fallback activated\", \"error\", storeErr\)\n\s+\}\n\s+sessionManager := session\.NewManagerWithStore\(morphismExecutor, dispatcher, cfg\.SessionTTL, cfg\.SessionCleanupEvery, logger, sessionStore\)",
    "sessionManager := session.NewManagerWithContainerStore(morphismExecutor, dispatcher, cfg.SessionTTL, cfg.SessionCleanupEvery, logger, containerStore)",
    text
)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("patched main.go")
