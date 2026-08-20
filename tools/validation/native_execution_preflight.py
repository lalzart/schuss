#!/usr/bin/env python3
"""Read-only authentication of the local ARM execution prerequisites."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from packages.schuss_core.gills_direct_backend import (  # noqa: E402
    DirectBackendError,
    DirectExecutionConfig,
    OBJECT_SOURCE_HASHES,
    RUNTIME_SOURCE_HASHES,
    TOOL_HASHES,
    verify_execution_config,
)


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _missing_external_inputs(config: DirectExecutionConfig) -> list[str]:
    required = {
        "patcher-checkout": config.patcher_root,
        "factory-checkout": config.factory_root,
        "contrib-checkout": config.contrib_root,
        "installed-runtime-elf": config.installed_firmware_elf,
    }
    required.update(
        {
            f"runtime-source:{relative}": config.patcher_root / relative
            for relative in RUNTIME_SOURCE_HASHES
        }
    )
    for locator in OBJECT_SOURCE_HASHES:
        source, relative = locator.split(":", 1)
        checkout = config.factory_root if source == "factory" else config.contrib_root
        required[f"object-source:{locator}"] = checkout / relative
    required.update(
        {
            f"arm-tool:{name}": config.arm_bin / name
            for name in TOOL_HASHES
        }
    )
    return sorted(
        label
        for label, path in required.items()
        if not path.exists()
    )


def main() -> int:
    config = DirectExecutionConfig.local_default()
    missing = _missing_external_inputs(config)
    if missing:
        print(
            _canonical(
                {
                    "schema_version": "schuss-native-execution-preflight-v1",
                    "status": "incomplete",
                    "diagnostic_code": "NATIVE_EXECUTION_PREREQUISITE_UNAVAILABLE",
                    "missing": missing,
                }
            ),
            file=sys.stderr,
        )
        return 3
    try:
        authenticated = verify_execution_config(config)
    except DirectBackendError as exc:
        status = (
            "incomplete"
            if exc.code.endswith("_UNAVAILABLE")
            else "failed"
        )
        print(
            _canonical(
                {
                    "schema_version": "schuss-native-execution-preflight-v1",
                    "status": status,
                    "diagnostic_code": exc.code,
                    "stage": exc.stage,
                    "subject": exc.subject,
                }
            ),
            file=sys.stderr,
        )
        return 3 if status == "incomplete" else 1
    except OSError:
        print(
            _canonical(
                {
                    "schema_version": "schuss-native-execution-preflight-v1",
                    "status": "incomplete",
                    "diagnostic_code": "NATIVE_EXECUTION_PREREQUISITE_UNAVAILABLE",
                }
            ),
            file=sys.stderr,
        )
        return 3

    print(
        _canonical(
            {
                "schema_version": "schuss-native-execution-preflight-v1",
                "status": "passed",
                "authenticated_execution": authenticated,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
