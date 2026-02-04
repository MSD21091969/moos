# Native Messaging

> How Chrome Extension accesses local filesystem for FILESYST domain.

## Overview

Chrome extensions are sandboxed and cannot directly access the filesystem. Native Messaging provides a secure bridge.

## Components

```
┌─────────────────────┐     JSON/stdin/stdout    ┌─────────────────────┐
│ CHROME EXTENSION    │◄────────────────────────►│ NATIVE HOST         │
│ (Service Worker)    │                          │ (Python executable) │
│                     │                          │                     │
│ chrome.runtime      │                          │ - File read/write   │
│ .sendNativeMessage()│                          │ - .agent/ access    │
└─────────────────────┘                          │ - Sync operations   │
                                                 └─────────────────────┘
```

## Setup Requirements

### 1. Native Host Executable

Python script that reads stdin, processes JSON, writes to stdout:

```python
# native_host.py
import sys, json, struct

def read_message():
    raw_length = sys.stdin.buffer.read(4)
    length = struct.unpack('I', raw_length)[0]
    message = sys.stdin.buffer.read(length).decode('utf-8')
    return json.loads(message)

def send_message(obj):
    encoded = json.dumps(obj).encode('utf-8')
    sys.stdout.buffer.write(struct.pack('I', len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()
```

### 2. Host Manifest (Windows Registry)

```json
{
  "name": "com.collider.agent_host",
  "description": "Collider Agent Native Host",
  "path": "C:\\path\\to\\native_host.exe",
  "type": "stdio",
  "allowed_origins": ["chrome-extension://EXTENSION_ID/"]
}
```

Registry key: `HKEY_CURRENT_USER\Software\Google\Chrome\NativeMessagingHosts\com.collider.agent_host`

### 3. Extension Permissions

```json
{
  "permissions": ["nativeMessaging"]
}
```

## Message Protocol

### Request (Extension → Host)

```json
{
  "action": "read_agent_context",
  "path": "D:\\FFS0_Factory\\workspaces\\FFS1_ColliderDataSystems\\.agent"
}
```

### Response (Host → Extension)

```json
{
  "success": true,
  "data": {
    "manifest": "...",
    "instructions": ["..."],
    "rules": ["..."]
  }
}
```

## Security

- Only registered extensions can connect
- Host only accesses permitted paths
- JSON-only communication (no arbitrary code execution)
