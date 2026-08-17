use serde::Serialize;
use serde_json::{Map, Value};
use std::collections::BTreeSet;
use std::env;
use std::ffi::OsString;
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::Mutex;

const CANONICAL_PROFILE: &str = "schuss-canonical-json-v1";
const MAX_REQUEST_BYTES: usize = 65_536;
const MAX_RESPONSE_BYTES: usize = 1_048_576;
const FILTER_NAMES: [&str; 10] = [
    "function",
    "abstraction",
    "form",
    "signal_domain",
    "signal_rate",
    "signal_role",
    "capability",
    "technique",
    "readiness",
    "provenance",
];

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct BridgeError {
    code: &'static str,
    message: &'static str,
}

impl BridgeError {
    fn new(code: &'static str, message: &'static str) -> Self {
        Self { code, message }
    }
}

struct BridgeProcess {
    child: Child,
    stdin: ChildStdin,
    stdout: BufReader<ChildStdout>,
}

impl Drop for BridgeProcess {
    fn drop(&mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}

pub struct ReadOnlyBridge {
    repository_root: PathBuf,
    process: Mutex<Option<BridgeProcess>>,
}

impl ReadOnlyBridge {
    pub fn from_repository_layout() -> Self {
        let manifest_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
        let repository_root = manifest_dir
            .ancestors()
            .nth(3)
            .expect("src-tauri must remain below apps/schuss_desktop")
            .to_path_buf();
        Self {
            repository_root,
            process: Mutex::new(None),
        }
    }

    fn python_executable() -> OsString {
        env::var_os("SCHUSS_DESKTOP_PYTHON").unwrap_or_else(|| OsString::from("python3"))
    }

    fn spawn_process(&self) -> Result<BridgeProcess, BridgeError> {
        let script = self
            .repository_root
            .join("apps/schuss_desktop/bridge/read_only_catalog_bridge.py");
        let mut child = Command::new(Self::python_executable())
            .arg(script)
            .current_dir(&self.repository_root)
            .env("PYTHONDONTWRITEBYTECODE", "1")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()
            .map_err(|_| {
                BridgeError::new(
                    "BRIDGE_PROCESS_START_FAILED",
                    "the local Schuss core process could not start",
                )
            })?;
        let stdin = child.stdin.take().ok_or_else(|| {
            BridgeError::new(
                "BRIDGE_PROCESS_START_FAILED",
                "the local Schuss core input stream is unavailable",
            )
        })?;
        let stdout = child.stdout.take().ok_or_else(|| {
            BridgeError::new(
                "BRIDGE_PROCESS_START_FAILED",
                "the local Schuss core output stream is unavailable",
            )
        })?;
        Ok(BridgeProcess {
            child,
            stdin,
            stdout: BufReader::new(stdout),
        })
    }

    fn exchange(process: &mut BridgeProcess, request: &[u8]) -> Result<Value, BridgeError> {
        process.stdin.write_all(request).map_err(|_| {
            BridgeError::new(
                "BRIDGE_TRANSPORT_FAILED",
                "the local Schuss core request could not be sent",
            )
        })?;
        process.stdin.write_all(b"\n").map_err(|_| {
            BridgeError::new(
                "BRIDGE_TRANSPORT_FAILED",
                "the local Schuss core request could not be terminated",
            )
        })?;
        process.stdin.flush().map_err(|_| {
            BridgeError::new(
                "BRIDGE_TRANSPORT_FAILED",
                "the local Schuss core request could not be flushed",
            )
        })?;

        let mut response = Vec::new();
        let count = process.stdout.read_until(b'\n', &mut response).map_err(|_| {
            BridgeError::new(
                "BRIDGE_TRANSPORT_FAILED",
                "the local Schuss core response could not be read",
            )
        })?;
        if count == 0 || !response.ends_with(b"\n") {
            return Err(BridgeError::new(
                "BRIDGE_PROCESS_ENDED",
                "the local Schuss core process ended without a result",
            ));
        }
        if response.len() > MAX_RESPONSE_BYTES {
            return Err(BridgeError::new(
                "BRIDGE_RESPONSE_TOO_LARGE",
                "the local Schuss core response exceeds the desktop bridge limit",
            ));
        }
        serde_json::from_slice(&response).map_err(|_| {
            BridgeError::new(
                "BRIDGE_RESPONSE_INVALID",
                "the local Schuss core response is not valid JSON",
            )
        })
    }

    fn dispatch(&self, request: Value) -> Result<Value, BridgeError> {
        let (operation, expected_result) = validate_request(&request)?;
        let request_bytes = serde_json::to_vec(&request).map_err(|_| {
            BridgeError::new(
                "BRIDGE_REQUEST_INVALID",
                "the desktop request could not be serialized",
            )
        })?;
        if request_bytes.len() > MAX_REQUEST_BYTES {
            return Err(BridgeError::new(
                "BRIDGE_REQUEST_TOO_LARGE",
                "the desktop request exceeds the bridge limit",
            ));
        }

        let mut guard = self.process.lock().map_err(|_| {
            BridgeError::new(
                "BRIDGE_STATE_UNAVAILABLE",
                "the local Schuss core bridge is unavailable",
            )
        })?;
        if guard.is_none() {
            *guard = Some(self.spawn_process()?);
        }
        let result = Self::exchange(guard.as_mut().expect("bridge process exists"), &request_bytes);
        let response = match result {
            Ok(value) => value,
            Err(error) => {
                *guard = None;
                return Err(error);
            }
        };
        validate_response(&response, operation, expected_result)?;
        Ok(response)
    }
}

#[tauri::command(async)]
pub fn dispatch_read_only_operation(
    bridge: tauri::State<'_, ReadOnlyBridge>,
    request: Value,
) -> Result<Value, BridgeError> {
    bridge.dispatch(request)
}

fn exact_keys(object: &Map<String, Value>, expected: &[&str]) -> bool {
    let observed: BTreeSet<&str> = object.keys().map(String::as_str).collect();
    let expected: BTreeSet<&str> = expected.iter().copied().collect();
    observed == expected
}

fn validate_request(request: &Value) -> Result<(&str, &str), BridgeError> {
    let object = request.as_object().ok_or_else(|| {
        BridgeError::new("BRIDGE_REQUEST_INVALID", "request must be an object")
    })?;
    if !exact_keys(
        object,
        &["canonical_profile", "operation", "payload", "schema_version"],
    ) {
        return Err(BridgeError::new(
            "BRIDGE_REQUEST_INVALID",
            "request fields do not match the shared operation envelope",
        ));
    }
    if object.get("canonical_profile").and_then(Value::as_str) != Some(CANONICAL_PROFILE) {
        return Err(BridgeError::new(
            "BRIDGE_CANONICAL_PROFILE_INVALID",
            "request must use the Schuss canonical JSON profile",
        ));
    }
    let operation = object.get("operation").and_then(Value::as_str).ok_or_else(|| {
        BridgeError::new("BRIDGE_REQUEST_INVALID", "operation must be a string")
    })?;
    let schema = object
        .get("schema_version")
        .and_then(Value::as_str)
        .ok_or_else(|| {
            BridgeError::new(
                "BRIDGE_REQUEST_VERSION_INVALID",
                "request schema version must be a string",
            )
        })?;
    let payload = object.get("payload").and_then(Value::as_object).ok_or_else(|| {
        BridgeError::new("BRIDGE_REQUEST_INVALID", "request payload must be an object")
    })?;

    match operation {
        "application.describe" => {
            if schema != "schuss-operation-request-v7"
                || !exact_keys(payload, &["scope"])
                || payload.get("scope").and_then(Value::as_str) != Some("selected-context")
            {
                return Err(BridgeError::new(
                    "BRIDGE_REQUEST_INVALID",
                    "application.describe does not match its shared request shape",
                ));
            }
            Ok((operation, "schuss-operation-result-v7"))
        }
        "catalog.search" => {
            validate_search_payload(payload)?;
            if schema != "schuss-operation-request-v2" {
                return Err(BridgeError::new(
                    "BRIDGE_REQUEST_VERSION_INVALID",
                    "catalog.search must use operation request v2",
                ));
            }
            Ok((operation, "schuss-operation-result-v2"))
        }
        "catalog.inspect" => {
            validate_inspect_payload(payload)?;
            if schema != "schuss-operation-request-v2" {
                return Err(BridgeError::new(
                    "BRIDGE_REQUEST_VERSION_INVALID",
                    "catalog.inspect must use operation request v2",
                ));
            }
            Ok((operation, "schuss-operation-result-v2"))
        }
        _ => Err(BridgeError::new(
            "BRIDGE_OPERATION_FORBIDDEN",
            "operation is not in the read-only desktop allowlist",
        )),
    }
}

fn validate_search_payload(payload: &Map<String, Value>) -> Result<(), BridgeError> {
    if !exact_keys(payload, &["filters", "query"])
        || payload.get("query").and_then(Value::as_str).is_none()
    {
        return Err(BridgeError::new(
            "BRIDGE_REQUEST_INVALID",
            "catalog.search query and filters are required",
        ));
    }
    let filters = payload
        .get("filters")
        .and_then(Value::as_object)
        .ok_or_else(|| {
            BridgeError::new(
                "BRIDGE_REQUEST_INVALID",
                "catalog.search filters must be an object",
            )
        })?;
    if !exact_keys(filters, &FILTER_NAMES) {
        return Err(BridgeError::new(
            "BRIDGE_REQUEST_INVALID",
            "catalog.search filters do not match the shared request shape",
        ));
    }
    for name in FILTER_NAMES {
        let values = filters.get(name).and_then(Value::as_array).ok_or_else(|| {
            BridgeError::new(
                "BRIDGE_REQUEST_INVALID",
                "each catalog.search filter must be an array",
            )
        })?;
        let mut unique = BTreeSet::new();
        for value in values {
            let text = value.as_str().filter(|item| !item.is_empty()).ok_or_else(|| {
                BridgeError::new(
                    "BRIDGE_REQUEST_INVALID",
                    "catalog.search filter values must be non-empty strings",
                )
            })?;
            if !unique.insert(text) {
                return Err(BridgeError::new(
                    "BRIDGE_REQUEST_INVALID",
                    "catalog.search filter values must be unique",
                ));
            }
        }
    }
    Ok(())
}

fn validate_inspect_payload(payload: &Map<String, Value>) -> Result<(), BridgeError> {
    if !exact_keys(payload, &["family_reference"]) {
        return Err(BridgeError::new(
            "BRIDGE_REQUEST_INVALID",
            "catalog.inspect requires one exact family reference",
        ));
    }
    let reference = payload
        .get("family_reference")
        .and_then(Value::as_object)
        .ok_or_else(|| {
            BridgeError::new(
                "BRIDGE_REQUEST_INVALID",
                "catalog.inspect family reference must be an object",
            )
        })?;
    if !exact_keys(reference, &["content_hash", "family_id", "revision"]) {
        return Err(BridgeError::new(
            "BRIDGE_REQUEST_INVALID",
            "catalog.inspect family reference is not exact",
        ));
    }
    let family_id = reference.get("family_id").and_then(Value::as_str).unwrap_or("");
    let suffix = family_id.strip_prefix("schuss-family-").unwrap_or("");
    let valid_family = suffix.len() == 6 && suffix.bytes().all(|byte| byte.is_ascii_digit());
    let valid_revision = reference
        .get("revision")
        .and_then(Value::as_u64)
        .is_some_and(|value| value > 0);
    let hash = reference
        .get("content_hash")
        .and_then(Value::as_str)
        .unwrap_or("");
    let hash_suffix = hash.strip_prefix("sha256:").unwrap_or("");
    let valid_hash = hash_suffix.len() == 64
        && hash_suffix
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte));
    if !valid_family || !valid_revision || !valid_hash {
        return Err(BridgeError::new(
            "BRIDGE_REQUEST_INVALID",
            "catalog.inspect family reference fields are invalid",
        ));
    }
    Ok(())
}

fn validate_response(
    response: &Value,
    operation: &str,
    expected_schema: &str,
) -> Result<(), BridgeError> {
    let object = response.as_object().ok_or_else(|| {
        BridgeError::new("BRIDGE_RESPONSE_INVALID", "core response must be an object")
    })?;
    if object.get("schema_version").and_then(Value::as_str)
        == Some("schuss-desktop-bridge-error-v1")
    {
        return Err(BridgeError::new(
            "BRIDGE_CORE_REJECTED",
            "the local Schuss core bridge rejected the request",
        ));
    }
    if !exact_keys(
        object,
        &[
            "canonical_profile",
            "diagnostics",
            "operation",
            "schema_version",
            "status",
            "value",
        ],
    ) || object.get("canonical_profile").and_then(Value::as_str) != Some(CANONICAL_PROFILE)
        || object.get("operation").and_then(Value::as_str) != Some(operation)
        || object.get("schema_version").and_then(Value::as_str) != Some(expected_schema)
        || object.get("diagnostics").and_then(Value::as_array).is_none()
        || object.get("status").and_then(Value::as_str).is_none()
    {
        return Err(BridgeError::new(
            "BRIDGE_RESPONSE_INVALID",
            "core response metadata does not match the read-only request",
        ));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn empty_filters() -> Value {
        json!({
            "function": [], "abstraction": [], "form": [], "signal_domain": [],
            "signal_rate": [], "signal_role": [], "capability": [], "technique": [],
            "readiness": [], "provenance": []
        })
    }

    #[test]
    fn allowlist_accepts_the_three_exact_shared_request_shapes() {
        let describe = json!({
            "schema_version": "schuss-operation-request-v7",
            "canonical_profile": CANONICAL_PROFILE,
            "operation": "application.describe",
            "payload": {"scope": "selected-context"}
        });
        let search = json!({
            "schema_version": "schuss-operation-request-v2",
            "canonical_profile": CANONICAL_PROFILE,
            "operation": "catalog.search",
            "payload": {"query": "", "filters": empty_filters()}
        });
        let inspect = json!({
            "schema_version": "schuss-operation-request-v2",
            "canonical_profile": CANONICAL_PROFILE,
            "operation": "catalog.inspect",
            "payload": {"family_reference": {
                "family_id": "schuss-family-000001",
                "revision": 1,
                "content_hash": format!("sha256:{}", "a".repeat(64))
            }}
        });
        assert_eq!(
            validate_request(&describe).unwrap(),
            ("application.describe", "schuss-operation-result-v7")
        );
        assert_eq!(
            validate_request(&search).unwrap(),
            ("catalog.search", "schuss-operation-result-v2")
        );
        assert_eq!(
            validate_request(&inspect).unwrap(),
            ("catalog.inspect", "schuss-operation-result-v2")
        );
    }

    #[test]
    fn allowlist_rejects_write_and_adjacent_read_operations() {
        for operation in ["graph.inspect", "graph.transact", "project.inspect", "build.plan"] {
            let request = json!({
                "schema_version": "schuss-operation-request-v1",
                "canonical_profile": CANONICAL_PROFILE,
                "operation": operation,
                "payload": {}
            });
            assert_eq!(
                validate_request(&request).unwrap_err().code,
                "BRIDGE_OPERATION_FORBIDDEN"
            );
        }
    }

    #[test]
    fn request_validation_rejects_version_payload_and_reference_drift() {
        let bad_search = json!({
            "schema_version": "schuss-operation-request-v3",
            "canonical_profile": CANONICAL_PROFILE,
            "operation": "catalog.search",
            "payload": {"query": "x", "filters": {}}
        });
        assert_eq!(
            validate_request(&bad_search).unwrap_err().code,
            "BRIDGE_REQUEST_INVALID"
        );

        let bad_inspect = json!({
            "schema_version": "schuss-operation-request-v2",
            "canonical_profile": CANONICAL_PROFILE,
            "operation": "catalog.inspect",
            "payload": {"family_reference": {
                "family_id": "latest",
                "revision": 0,
                "content_hash": "sha256:nope"
            }}
        });
        assert_eq!(
            validate_request(&bad_inspect).unwrap_err().code,
            "BRIDGE_REQUEST_INVALID"
        );
    }

    #[test]
    fn response_validation_rejects_schema_or_operation_substitution() {
        let response = json!({
            "schema_version": "schuss-operation-result-v2",
            "canonical_profile": CANONICAL_PROFILE,
            "operation": "catalog.inspect",
            "status": "success",
            "value": {},
            "diagnostics": []
        });
        assert_eq!(
            validate_response(&response, "catalog.search", "schuss-operation-result-v2")
                .unwrap_err()
                .code,
            "BRIDGE_RESPONSE_INVALID"
        );
    }
}
