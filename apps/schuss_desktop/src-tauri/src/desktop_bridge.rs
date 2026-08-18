use serde::Serialize;
use serde_json::{json, Map, Value};
use std::collections::BTreeSet;
use std::env;
use std::ffi::OsString;
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::Mutex;

const CANONICAL_PROFILE: &str = "schuss-canonical-json-v1";
const MAX_REQUEST_BYTES: usize = 262_144;
const MAX_RESPONSE_BYTES: usize = 4_194_304;

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

pub struct DesktopBridge {
    repository_root: PathBuf,
    process: Mutex<Option<BridgeProcess>>,
}

impl DesktopBridge {
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
            .join("apps/schuss_desktop/bridge/desktop_core_bridge.py");
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

    pub fn prepare(&self) -> Result<(), BridgeError> {
        let mut guard = self.process.lock().map_err(|_| {
            BridgeError::new(
                "BRIDGE_STATE_UNAVAILABLE",
                "the local Schuss core bridge is unavailable",
            )
        })?;
        if guard.is_none() {
            *guard = Some(self.spawn_process()?);
        }
        Ok(())
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

    fn dispatch(&self, request: Value, workspace: Option<String>) -> Result<Value, BridgeError> {
        let (operation, expected_result, requires_workspace) = validate_request(&request)?;
        validate_workspace(workspace.as_deref(), requires_workspace)?;
        let envelope = json!({"request": request, "workspace": workspace});
        let request_bytes = serde_json::to_vec(&envelope).map_err(|_| {
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
pub fn dispatch_desktop_operation(
    bridge: tauri::State<'_, DesktopBridge>,
    request: Value,
    workspace: Option<String>,
) -> Result<Value, BridgeError> {
    bridge.dispatch(request, workspace)
}

fn exact_keys(object: &Map<String, Value>, expected: &[&str]) -> bool {
    let observed: BTreeSet<&str> = object.keys().map(String::as_str).collect();
    let expected: BTreeSet<&str> = expected.iter().copied().collect();
    observed == expected
}

fn operation_versions(operation: &str) -> Option<(&'static str, &'static str, bool)> {
    match operation {
        "application.describe" => Some(("schuss-operation-request-v7", "schuss-operation-result-v7", false)),
        "catalog.implementations.search" => Some(("schuss-operation-request-v10", "schuss-operation-result-v10", false)),
        "catalog.inspect" | "catalog.search" => Some(("schuss-operation-request-v2", "schuss-operation-result-v2", false)),
        "component.inspect" => Some(("schuss-operation-request-v11", "schuss-operation-result-v11", false)),
        "build.session.start" | "build.session.inspect" | "device.session.discover" | "device.session.inspect" | "device.upload.start" | "device.upload.inspect" => Some(("schuss-operation-request-v12", "schuss-operation-result-v12", true)),
        "graph.inspect" => Some(("schuss-operation-request-v1", "schuss-operation-result-v1", false)),
        "graph.transact" | "project.profile.transact" => Some(("schuss-operation-request-v11", "schuss-operation-result-v11", true)),
        "project.history.inspect" | "project.profile.fork" | "project.revert" => Some(("schuss-operation-request-v8", "schuss-operation-result-v8", true)),
        "project.init" | "project.inspect" | "project.validate" => Some(("schuss-operation-request-v3", "schuss-operation-result-v3", true)),
        "project.object.inspect" | "project.objects.list" => Some(("schuss-operation-request-v13", "schuss-operation-result-v13", true)),
        "workspace.project.create" | "workspace.projects.list" => Some(("schuss-operation-request-v14", "schuss-operation-result-v14", true)),
        _ => None,
    }
}

fn validate_request(request: &Value) -> Result<(&str, &str, bool), BridgeError> {
    let object = request.as_object().ok_or_else(|| {
        BridgeError::new("BRIDGE_REQUEST_INVALID", "request must be an object")
    })?;
    if !exact_keys(
        object,
        &["canonical_profile", "operation", "payload", "schema_version"],
    ) || !object.get("payload").is_some_and(Value::is_object)
    {
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
    let (expected_request, expected_result, requires_workspace) =
        operation_versions(operation).ok_or_else(|| {
            BridgeError::new(
                "BRIDGE_OPERATION_FORBIDDEN",
                "operation is not in the desktop allowlist",
            )
        })?;
    if object.get("schema_version").and_then(Value::as_str) != Some(expected_request) {
        return Err(BridgeError::new(
            "BRIDGE_REQUEST_VERSION_INVALID",
            "operation request schema does not match the allowlist",
        ));
    }
    Ok((operation, expected_result, requires_workspace))
}

fn validate_workspace(workspace: Option<&str>, required: bool) -> Result<(), BridgeError> {
    if required && workspace.is_none() {
        return Err(BridgeError::new(
            "BRIDGE_WORKSPACE_REQUIRED",
            "operation requires one explicit project workspace",
        ));
    }
    if let Some(value) = workspace {
        if value.is_empty() || !Path::new(value).is_absolute() {
            return Err(BridgeError::new(
                "BRIDGE_WORKSPACE_INVALID",
                "workspace must be one explicit absolute path",
            ));
        }
    }
    Ok(())
}

fn validate_response(
    response: &Value,
    operation: &str,
    expected_result: &str,
) -> Result<(), BridgeError> {
    let object = response.as_object().ok_or_else(|| {
        BridgeError::new("BRIDGE_RESPONSE_INVALID", "core response must be an object")
    })?;
    if object.contains_key("error") {
        return Err(BridgeError::new(
            "BRIDGE_CORE_REJECTED",
            "the local Schuss core rejected the desktop request",
        ));
    }
    if object.get("operation").and_then(Value::as_str) != Some(operation)
        || object.get("schema_version").and_then(Value::as_str) != Some(expected_result)
        || object.get("canonical_profile").and_then(Value::as_str) != Some(CANONICAL_PROFILE)
        || !object.get("diagnostics").is_some_and(Value::is_array)
        || object.get("status").and_then(Value::as_str).is_none()
    {
        return Err(BridgeError::new(
            "BRIDGE_RESPONSE_INVALID",
            "core result metadata does not match the desktop request",
        ));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn request(operation: &str, schema: &str) -> Value {
        json!({
            "schema_version": schema,
            "canonical_profile": CANONICAL_PROFILE,
            "operation": operation,
            "payload": {}
        })
    }

    #[test]
    fn allowlist_is_closed_and_versioned() {
        assert!(validate_request(&request(
            "component.inspect",
            "schuss-operation-request-v11"
        ))
        .is_ok());
        assert!(validate_request(&request(
            "build.session.start",
            "schuss-operation-request-v12"
        ))
        .is_ok());
        assert!(validate_request(&request(
            "project.objects.list",
            "schuss-operation-request-v13"
        ))
        .is_ok());
        assert!(validate_request(&request(
            "workspace.projects.list",
            "schuss-operation-request-v14"
        ))
        .is_ok());
        assert!(validate_request(&request(
            "authoring.draft.create",
            "schuss-operation-request-v13"
        ))
        .is_err());
        assert!(validate_request(&request("build.execute", "schuss-operation-request-v5")).is_err());
        assert!(validate_request(&request("component.inspect", "schuss-operation-request-v1")).is_err());
    }

    #[test]
    fn workspace_is_explicit_for_project_writes() {
        assert!(validate_workspace(None, true).is_err());
        assert!(validate_workspace(Some("relative"), true).is_err());
        assert!(validate_workspace(Some("/tmp/schuss-project"), true).is_ok());
    }

    #[test]
    fn response_metadata_must_match() {
        let response = json!({
            "schema_version": "schuss-operation-result-v11",
            "canonical_profile": CANONICAL_PROFILE,
            "operation": "component.inspect",
            "status": "success",
            "value": {},
            "diagnostics": []
        });
        assert!(validate_response(
            &response,
            "component.inspect",
            "schuss-operation-result-v11"
        )
        .is_ok());
        assert!(validate_response(&response, "graph.inspect", "schuss-operation-result-v1").is_err());
    }
}
