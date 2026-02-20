"""Compile .proto files to Python gRPC stubs.

Usage:
    python -m proto.compile_protos

Generates *_pb2.py and *_pb2_grpc.py files in the proto/ directory,
importable by both DataServer and GraphToolServer.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


def main() -> None:
    proto_dir = Path(__file__).parent
    proto_files = list(proto_dir.glob("*.proto"))

    if not proto_files:
        print("No .proto files found in", proto_dir)
        sys.exit(1)

    for proto in proto_files:
        print(f"Compiling {proto.name}...")
        cmd = [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            f"--proto_path={proto_dir}",
            f"--python_out={proto_dir}",
            f"--grpc_python_out={proto_dir}",
            f"--pyi_out={proto_dir}",
            str(proto),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ERROR: {result.stderr}")
            sys.exit(1)
            
        # Fix imports in generated pb2_grpc.py files for Python 3
        grpc_file = proto_dir / f"{proto.stem}_pb2_grpc.py"
        if grpc_file.exists():
            content = grpc_file.read_text(encoding="utf-8")
            # Replace `import foo_pb2 as ...` with `from . import foo_pb2 as ...`
            content = re.sub(
                r"^import (.+_pb2) as (.+)",
                r"from . import \1 as \2",
                content,
                flags=re.MULTILINE
            )
            grpc_file.write_text(content, encoding="utf-8")
            
        print(f"  OK -> {proto.stem}_pb2.py, {proto.stem}_pb2_grpc.py")

    # Create __init__.py for importability
    init_file = proto_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text('"""Compiled protobuf stubs."""\n')
        print("  Created __init__.py")

    print("Done.")


if __name__ == "__main__":
    main()
