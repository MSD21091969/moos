"""
Native Messaging Host Installer
Registers the native host with Chrome/Edge browsers

Usage:
  python install.py [--uninstall]
"""

import os
import sys
import json
import winreg
from pathlib import Path

HOST_NAME = "com.collider.filesyst"
HOST_DESCRIPTION = "Collider FILESYST Native Messaging Host"


def get_manifest_path() -> Path:
    """Get the path where manifest should be installed"""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise RuntimeError("LOCALAPPDATA environment variable not set")

    return (
        Path(local_app_data)
        / "Google"
        / "Chrome"
        / "NativeMessagingHosts"
        / f"{HOST_NAME}.json"
    )


def get_host_path() -> Path:
    """Get the path to the native host script"""
    return Path(__file__).parent / "host.py"


def create_manifest(extension_id: str | None = None) -> dict:
    """Create the native messaging manifest"""
    host_path = get_host_path()

    # Use pythonw.exe for no console window
    python_exe = Path(sys.executable).parent / "pythonw.exe"
    if not python_exe.exists():
        python_exe = Path(sys.executable)  # Fall back to python.exe

    manifest = {
        "name": HOST_NAME,
        "description": HOST_DESCRIPTION,
        "path": str(python_exe),
        "type": "stdio",
        "allowed_origins": [],
    }

    # Add specific extension ID if provided
    if extension_id:
        manifest["allowed_origins"].append(f"chrome-extension://{extension_id}/")
    else:
        # For development: allow all extensions (not recommended for production)
        manifest["allowed_origins"].append("chrome-extension://*/*")

    return manifest


def install(extension_id: str | None = None) -> None:
    """Install the native messaging host"""
    manifest_path = get_manifest_path()

    # Create directory if needed
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # Write manifest
    manifest = create_manifest(extension_id)
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"✓ Manifest written to: {manifest_path}")

    # Also register in Windows Registry (required for some Chrome versions)
    try:
        key_path = rf"Software\Google\Chrome\NativeMessagingHosts\{HOST_NAME}"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(manifest_path))
        print(f"✓ Registry key created: HKCU\\{key_path}")
    except Exception as e:
        print(f"⚠ Could not create registry key: {e}")

    print(f"\n✓ Native host '{HOST_NAME}' installed successfully!")
    print(f"  Host script: {get_host_path()}")
    print(f"  Allowed origins: {manifest['allowed_origins']}")


def uninstall() -> None:
    """Uninstall the native messaging host"""
    manifest_path = get_manifest_path()

    # Remove manifest file
    if manifest_path.exists():
        manifest_path.unlink()
        print(f"✓ Manifest removed: {manifest_path}")
    else:
        print(f"⚠ Manifest not found: {manifest_path}")

    # Remove registry key
    try:
        key_path = rf"Software\Google\Chrome\NativeMessagingHosts\{HOST_NAME}"
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        print(f"✓ Registry key removed: HKCU\\{key_path}")
    except FileNotFoundError:
        print(f"⚠ Registry key not found")
    except Exception as e:
        print(f"⚠ Could not remove registry key: {e}")

    print(f"\n✓ Native host '{HOST_NAME}' uninstalled")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--uninstall":
        uninstall()
    else:
        # Get extension ID from args or environment
        extension_id = None
        if len(sys.argv) > 1:
            extension_id = sys.argv[1]
        elif os.environ.get("COLLIDER_EXTENSION_ID"):
            extension_id = os.environ["COLLIDER_EXTENSION_ID"]

        install(extension_id)


if __name__ == "__main__":
    main()
