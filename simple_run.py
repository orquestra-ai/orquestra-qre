#!/usr/bin/env python3
"""Simple web server to run Orquestra QRE without Tauri complexity."""

import webbrowser
import threading
import time
from orquestra_qre.cli import main

def open_browser():
    """Open browser after a short delay."""
    time.sleep(2)
    webbrowser.open('http://localhost:8080')

if __name__ == "__main__":
    # Start browser in background
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    print("🚀 Starting Orquestra QRE Platform...")
    print("🌐 Web interface will open at: http://localhost:8080")
    print("💡 Press Ctrl+C to stop")
    
    # Run the platform
    main()
