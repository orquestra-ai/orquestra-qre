// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;

// Learn more about Tauri commands at https://tauri.app/v1/guides/features/command
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! This message comes from Rust!", name)
}

fn main() {
    println!("Starting Tauri application...");
    
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![greet])
        .setup(|app| {
            println!("Tauri app setup complete");
            
            // Get the main window and ensure it's visible
            let window = app.get_window("main").unwrap();
            window.show().unwrap();
            window.set_focus().unwrap();
            
            println!("Window should now be visible");
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
        
    println!("Tauri application exited");
}
