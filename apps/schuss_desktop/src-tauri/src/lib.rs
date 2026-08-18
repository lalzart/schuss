mod desktop_bridge;

use desktop_bridge::{dispatch_desktop_operation, DesktopBridge};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(DesktopBridge::from_repository_layout())
        .invoke_handler(tauri::generate_handler![dispatch_desktop_operation])
        .run(tauri::generate_context!())
        .expect("Schuss desktop runtime failed");
}
