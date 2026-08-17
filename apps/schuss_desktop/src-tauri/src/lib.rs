mod read_only_bridge;

use read_only_bridge::{dispatch_read_only_operation, ReadOnlyBridge};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(ReadOnlyBridge::from_repository_layout())
        .invoke_handler(tauri::generate_handler![dispatch_read_only_operation])
        .run(tauri::generate_context!())
        .expect("Schuss desktop runtime failed");
}
