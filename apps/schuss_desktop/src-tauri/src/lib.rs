mod desktop_bridge;

use desktop_bridge::{dispatch_desktop_operation, DesktopBridge};
use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(DesktopBridge::from_repository_layout())
        .setup(|app| {
            // Spawning is non-blocking with respect to the Python core's
            // repository initialization. The window can render its shell while
            // the persistent process prepares the accepted record set.
            let _ = app.state::<DesktopBridge>().prepare();
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![dispatch_desktop_operation])
        .run(tauri::generate_context!())
        .expect("Schuss desktop runtime failed");
}
