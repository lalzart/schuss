#!/usr/bin/env python3
"""Deterministic, dependency-free helpers for Instrument Lab v1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any


class ContractError(RuntimeError):
    """Stable fail-closed contract error."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def _object_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError("DUPLICATE_JSON_KEY", key)
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_object_no_duplicates)
    except ContractError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("INVALID_JSON", f"{path}: {exc}") from exc


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ContractError("MISSING_AUTHORITY", str(path)) from exc
    return digest.hexdigest()


def relative_authority_path(raw: Any) -> PurePosixPath:
    if not isinstance(raw, str) or not raw:
        raise ContractError("INVALID_AUTHORITY_PATH", repr(raw))
    if "latest" in raw.lower() or "\\" in raw:
        raise ContractError("AMBIGUOUS_AUTHORITY_PATH", raw)
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ContractError("ESCAPING_AUTHORITY_PATH", raw)
    return path


def exact_keys(value: Any, expected: set[str], where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("INVALID_OBJECT", where)
    unknown = sorted(set(value) - expected)
    missing = sorted(expected - set(value))
    if unknown:
        raise ContractError("UNKNOWN_FIELD", f"{where}: {', '.join(unknown)}")
    if missing:
        raise ContractError("MISSING_FIELD", f"{where}: {', '.join(missing)}")
    return value


def string_list(value: Any, where: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise ContractError("INVALID_STRING_LIST", where)
    if not all(isinstance(item, str) and item for item in value):
        raise ContractError("INVALID_STRING_LIST", where)
    return value

