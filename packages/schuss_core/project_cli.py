"""Task 012A project CLI request construction and deterministic presentation."""

from __future__ import annotations

import re
from typing import Any

from .product_cli import ProductInputError, _append_tree, _safe_text


PROJECT_LOCATOR_RE = re.compile(
    r"^(?P<project_id>schuss-project-[0-9]{6})@(?P<revision>[1-9][0-9]*)$"
)
GRAPH_LOCATOR_RE = re.compile(
    r"^(?P<graph_id>schuss-graph-[0-9]{6})@(?P<revision>[1-9][0-9]*)$"
)
CONTENT_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
PROJECT_ID_RE = re.compile(r"^schuss-project-[0-9]{6}$")


def exact_project_reference(locator: str, content_hash: str) -> dict[str, Any]:
    match = PROJECT_LOCATOR_RE.fullmatch(locator)
    if match is None:
        raise ProductInputError(
            "CLI_PROJECT_LOCATOR_MALFORMED",
            "expected project locator schuss-project-NNNNNN@REVISION",
        )
    if CONTENT_HASH_RE.fullmatch(content_hash) is None:
        raise ProductInputError(
            "CLI_PROJECT_HASH_MALFORMED",
            "expected project content hash sha256 followed by 64 lowercase hexadecimal digits",
        )
    return {
        "project_id": match.group("project_id"),
        "revision": int(match.group("revision")),
        "content_hash": content_hash,
    }


def exact_graph_reference(locator: str, content_hash: str) -> dict[str, Any]:
    match = GRAPH_LOCATOR_RE.fullmatch(locator)
    if match is None:
        raise ProductInputError(
            "CLI_LOCATOR_MALFORMED",
            "expected graph locator schuss-graph-NNNNNN@REVISION",
        )
    if CONTENT_HASH_RE.fullmatch(content_hash) is None:
        raise ProductInputError(
            "CLI_GRAPH_HASH_MALFORMED",
            "expected graph content hash sha256 followed by 64 lowercase hexadecimal digits",
        )
    return {
        "graph_id": match.group("graph_id"),
        "revision": int(match.group("revision")),
        "content_hash": content_hash,
    }


def project_init_request(
    project_id: str,
    base_record_set: dict[str, Any],
    primary_graph_reference: dict[str, Any],
    instrument_references: list[dict[str, Any]],
    build_request_references: list[dict[str, Any]],
) -> dict[str, Any]:
    if PROJECT_ID_RE.fullmatch(project_id) is None:
        raise ProductInputError(
            "CLI_PROJECT_ID_MALFORMED",
            "expected opaque project ID schuss-project-NNNNNN",
        )
    return {
        "schema_version": "schuss-operation-request-v3",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "project.init",
        "payload": {
            "project_id": project_id,
            "base_record_set": base_record_set,
            "primary_graph_reference": primary_graph_reference,
            "instrument_references": instrument_references,
            "build_request_references": build_request_references,
            "asset_references": [],
        },
    }


def project_inspect_request() -> dict[str, Any]:
    return {
        "schema_version": "schuss-operation-request-v3",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "project.inspect",
        "payload": {"scope": "accepted-project"},
    }


def project_validate_request() -> dict[str, Any]:
    return {
        "schema_version": "schuss-operation-request-v3",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "project.validate",
        "payload": {"scope": "accepted-project"},
    }


def project_graph_commit_request(
    expected_project_reference: dict[str, Any],
    graph_reference: dict[str, Any],
    edits: list[Any],
) -> dict[str, Any]:
    return {
        "schema_version": "schuss-operation-request-v3",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "project.graph.commit",
        "payload": {
            "expected_project_reference": expected_project_reference,
            "graph_reference": graph_reference,
            "base_content_hash": graph_reference["content_hash"],
            "edits": edits,
            "write_intent": "explicit",
        },
    }


def project_profile_fork_request(
    expected_project_reference: dict[str, Any],
    template_graph_reference: dict[str, Any],
    template_instrument_reference: dict[str, Any],
    template_build_request_reference: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "schuss-operation-request-v8",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "project.profile.fork",
        "payload": {
            "expected_project_reference": expected_project_reference,
            "template_graph_reference": template_graph_reference,
            "template_instrument_reference": template_instrument_reference,
            "template_build_request_reference": template_build_request_reference,
            "write_intent": "explicit",
        },
    }


def project_profile_transact_request(
    expected_project_reference: dict[str, Any],
    graph_reference: dict[str, Any],
    edits: list[Any],
) -> dict[str, Any]:
    return {
        "schema_version": "schuss-operation-request-v8",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "project.profile.transact",
        "payload": {
            "expected_project_reference": expected_project_reference,
            "graph_reference": graph_reference,
            "base_content_hash": graph_reference["content_hash"],
            "edits": edits,
            "write_intent": "explicit",
        },
    }


def project_history_request() -> dict[str, Any]:
    return {
        "schema_version": "schuss-operation-request-v8",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "project.history.inspect",
        "payload": {"scope": "immutable-ancestry"},
    }


def project_revert_request(
    expected_project_reference: dict[str, Any],
    target_project_reference: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "schuss-operation-request-v8",
        "canonical_profile": "schuss-canonical-json-v1",
        "operation": "project.revert",
        "payload": {
            "expected_project_reference": expected_project_reference,
            "target_project_reference": target_project_reference,
            "write_intent": "explicit",
        },
    }


def _reference_text(reference: dict[str, Any]) -> str:
    for field in (
        "project_id",
        "record_set_id",
        "graph_id",
        "instrument_id",
        "build_request_id",
    ):
        if field in reference:
            return f"{_safe_text(reference[field])}@{reference['revision']}"
    return "unknown-reference"


def render_project_result(result: dict[str, Any]) -> bytes:
    lines = [
        f"operation: {result['operation']}",
        f"status: {result['status']}",
    ]
    value = result.get("value")
    if value is not None:
        project = value.get("project")
        if project is not None:
            reference = {
                "project_id": project["project_id"],
                "revision": project["revision"],
                "content_hash": project["content_hash"],
            }
            lines.append(f"project: {_reference_text(reference)}")
            lines.append(f"project_content_hash: {reference['content_hash']}")
            base = project["base_record_set"]["reference"]
            lines.append(f"base_record_set: {_reference_text(base)}")
            lines.append(f"base_record_set_content_hash: {base['content_hash']}")
            graph = project["primary_graph_reference"]
            lines.append(f"primary_graph: {_reference_text(graph)}")
            lines.append(f"primary_graph_content_hash: {graph['content_hash']}")
            lines.append(f"owned_member_count: {len(project['owned_members'])}")
        elif "project_reference" in value:
            reference = value["project_reference"]
            lines.append(f"project: {_reference_text(reference)}")
            lines.append(f"project_content_hash: {reference['content_hash']}")
            graph = value["primary_graph_reference"]
            lines.append(f"primary_graph: {_reference_text(graph)}")
            lines.append(f"primary_graph_content_hash: {graph['content_hash']}")
        if "persistence_status" in value:
            lines.append(f"persistence_status: {value['persistence_status']}")
        if "acceptance_boundary" in value:
            lines.append(f"acceptance_boundary: {value['acceptance_boundary']}")
        if "write_plan" in value:
            lines.append(
                f"write_plan_content_hash: {value['write_plan']['content_hash']}"
            )
        validation = value.get("validation") or value.get("summary")
        if validation is not None:
            lines.append("validation:")
            _append_tree(lines, validation, "  ")
        if "durable_files" in value:
            lines.append("durable_files:")
            _append_tree(lines, value["durable_files"], "  ")
            lines.append("local_state:")
            _append_tree(lines, value["local_state"], "  ")
        if "graph_transaction_result" in value:
            lines.append(
                "graph_transaction_status: "
                + value["graph_transaction_result"]["status"]
            )
        if "head_project_reference" in value:
            lines.append(
                "head_project: " + _reference_text(value["head_project_reference"])
            )
            lines.append(f"revision_count: {value['revision_count']}")
            lines.append("ancestry:")
            _append_tree(lines, value["ancestry"], "  ")
    lines.append("diagnostics:")
    if not result["diagnostics"]:
        lines.append("  none")
    else:
        for diagnostic in result["diagnostics"]:
            lines.append(f"  - severity: {_safe_text(diagnostic['severity'])}")
            lines.append(f"    code: {_safe_text(diagnostic['code'])}")
            lines.append(f"    subject: {_safe_text(diagnostic['subject'])}")
            lines.append(f"    location: {_safe_text(diagnostic['location'])}")
            lines.append(f"    message: {_safe_text(diagnostic['message'])}")
    return ("\n".join(lines) + "\n").encode("utf-8")


PROJECT_BASH_COMPLETION = """# Schuss Task 012A project completion for Bash
_schuss_project_complete() {
  local current="${COMP_WORDS[COMP_CWORD]}"
  local choices=""
  if [[ ${COMP_CWORD} -eq 1 ]]; then
    choices="project"
  elif [[ ${COMP_CWORD} -eq 2 ]]; then
    choices="create edit init inspect validate history revert transact op completion --help"
  else
    case "${COMP_WORDS[2]}" in
      create) choices="--project --project-id --record-set --json --help" ;;
      edit) choices="--project --expected-project --project-content-hash --graph-content-hash --edits --write --json --help" ;;
      init) choices="--project --project-id --record-set --graph --instrument --build-request --json --help" ;;
      inspect|validate|history) choices="--project --json --help" ;;
      revert) choices="--project --expected-project --project-content-hash --target-project --target-content-hash --write --json --help" ;;
      transact) choices="--project --expected-project --project-content-hash --graph-content-hash --edits --write --json --help" ;;
      op) choices="--project --request --json --help" ;;
      completion) choices="bash zsh fish --help" ;;
    esac
  fi
  COMPREPLY=( $(compgen -W "${choices}" -- "${current}") )
}
complete -F _schuss_project_complete schuss
"""

PROJECT_ZSH_COMPLETION = """#compdef schuss
# Schuss Task 012A project completion for Zsh
_schuss_project() {
  local -a project_commands shells
  project_commands=(create edit init inspect validate history revert transact op completion)
  shells=(bash zsh fish)
  if (( CURRENT == 2 )); then
    _values 'command' project
  elif (( CURRENT == 3 )); then
    _describe 'project command' project_commands
  else
    case ${words[3]} in
      create) _values 'option' --project --project-id --record-set --json --help ;;
      edit) _values 'option' --project --expected-project --project-content-hash --graph-content-hash --edits --write --json --help ;;
      init) _values 'option' --project --project-id --record-set --graph --instrument --build-request --json --help ;;
      inspect|validate|history) _values 'option' --project --json --help ;;
      revert) _values 'option' --project --expected-project --project-content-hash --target-project --target-content-hash --write --json --help ;;
      transact) _values 'option' --project --expected-project --project-content-hash --graph-content-hash --edits --write --json --help ;;
      op) _values 'option' --project --request --json --help ;;
      completion) _describe 'shell' shells ;;
    esac
  fi
}
_schuss_project "$@"
"""

PROJECT_FISH_COMPLETION = """# Schuss Task 012A project completion for Fish
complete -c schuss -f
complete -c schuss -n '__fish_use_subcommand' -a project
complete -c schuss -n '__fish_seen_subcommand_from project' -a 'create edit init inspect validate history revert transact op completion'
complete -c schuss -n '__fish_seen_subcommand_from create edit init inspect validate history revert transact op' -l project -r
complete -c schuss -n '__fish_seen_subcommand_from create init' -l project-id -r
complete -c schuss -n '__fish_seen_subcommand_from create init' -l record-set -r
complete -c schuss -n '__fish_seen_subcommand_from init' -l graph -r
complete -c schuss -n '__fish_seen_subcommand_from init' -l instrument -r
complete -c schuss -n '__fish_seen_subcommand_from init' -l build-request -r
complete -c schuss -n '__fish_seen_subcommand_from transact' -l expected-project -r
complete -c schuss -n '__fish_seen_subcommand_from transact' -l project-content-hash -r
complete -c schuss -n '__fish_seen_subcommand_from transact' -l graph-content-hash -r
complete -c schuss -n '__fish_seen_subcommand_from transact' -l edits -r
complete -c schuss -n '__fish_seen_subcommand_from transact' -l write
complete -c schuss -n '__fish_seen_subcommand_from edit' -l expected-project -r
complete -c schuss -n '__fish_seen_subcommand_from edit' -l project-content-hash -r
complete -c schuss -n '__fish_seen_subcommand_from edit' -l graph-content-hash -r
complete -c schuss -n '__fish_seen_subcommand_from edit' -l edits -r
complete -c schuss -n '__fish_seen_subcommand_from edit' -l write
complete -c schuss -n '__fish_seen_subcommand_from revert' -l expected-project -r
complete -c schuss -n '__fish_seen_subcommand_from revert' -l project-content-hash -r
complete -c schuss -n '__fish_seen_subcommand_from revert' -l target-project -r
complete -c schuss -n '__fish_seen_subcommand_from revert' -l target-content-hash -r
complete -c schuss -n '__fish_seen_subcommand_from revert' -l write
complete -c schuss -n '__fish_seen_subcommand_from op' -l request -r
complete -c schuss -n '__fish_seen_subcommand_from create edit init inspect validate history revert transact' -l json
complete -c schuss -l help
"""

PROJECT_COMPLETION_SCRIPTS = {
    "bash": PROJECT_BASH_COMPLETION,
    "zsh": PROJECT_ZSH_COMPLETION,
    "fish": PROJECT_FISH_COMPLETION,
}


def project_completion_script(shell: str) -> bytes:
    return PROJECT_COMPLETION_SCRIPTS[shell].encode("utf-8")
