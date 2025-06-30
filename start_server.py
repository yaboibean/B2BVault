#!/usr/bin/env python3
import os
import http.server
import socketserver
import webbrowser
import time

def start_server():
    website_dir = r"scraped_data/website"
    PORT = 8000
    
    if not os.path.exists(website_dir):
        print("❌ Website directory not found!")
        return
        
    os.chdir(website_dir)
    Handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"🌐 B2B Vault Analysis Website")
            print(f"🚀 Server running at http://localhost:{PORT}")
            print("📱 Opening in your browser...")
            print("⏹️  Press Ctrl+C to stop the server")
            
            time.sleep(1)
            webbrowser.open(f'http://localhost:{PORT}')
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n✅ Server stopped.")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {PORT} is already in use. Try a different port or stop the existing server.")
        else:
            print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    start_server()
