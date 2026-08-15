#!/usr/bin/env python3
"""Run one pinned GNU Arm tool and append its exact vector and status."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


def main() -> int:
    tool = Path(sys.argv[0]).name
    real_root = os.environ.get("SCHUSS_REAL_ARM_BIN")
    log_path = os.environ.get("SCHUSS_ARM_COMMAND_LOG")
    if not real_root or not log_path or not tool.startswith("arm-none-eabi-"):
        print("task009 ARM wrapper is missing its explicit configuration", file=sys.stderr)
        return 125
    executable = Path(real_root) / tool
    result = subprocess.run([str(executable), *sys.argv[1:]], check=False)
    record = {
        "arguments": [str(executable), *sys.argv[1:]],
        "exit_status": result.returncode,
        "working_directory": os.getcwd(),
    }
    payload = json.dumps(record, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
    descriptor = os.open(log_path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, payload.encode("utf-8"))
    finally:
        os.close(descriptor)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
