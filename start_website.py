#!/usr/bin/env python3
"""
Simple script to start the B2B Vault Analysis website
"""
import os
import http.server
import socketserver
import webbrowser
import sys
import time

def start_server():
    website_dir = os.path.join(os.path.dirname(__file__), "scraped_data", "website")
    
    if not os.path.exists(website_dir):
        print("❌ Website not found. Please run the scraper first to generate the website.")
        print("Run: python3 B2Bscraper.py")
        return
    
    if not os.path.exists(os.path.join(website_dir, "index.html")):
        print("❌ Website index.html not found. Please run the scraper first.")
        return
    
    # Try different ports if 8000 is busy
    ports_to_try = [8000, 8001, 8002, 8003, 8080]
    
    for PORT in ports_to_try:
        try:
            os.chdir(website_dir)
            Handler = http.server.SimpleHTTPRequestHandler
            
            with socketserver.TCPServer(("", PORT), Handler) as httpd:
                print(f"🌐 B2B Vault Analysis Website")
                print(f"🚀 Server running at http://localhost:{PORT}")
                print(f"📁 Serving files from: {website_dir}")
                print("📱 Opening in your browser...")
                print("⏹️  Press Ctrl+C to stop the server")
                print("-" * 50)
                
                # Give the server a moment to start
                time.sleep(1)
                webbrowser.open(f'http://localhost:{PORT}')
                httpd.serve_forever()
                
        except KeyboardInterrupt:
            print("\n✅ Server stopped.")
            break
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"⚠️  Port {PORT} is busy, trying next port...")
                continue
            else:
                print(f"❌ Error starting server on port {PORT}: {e}")
                continue
    else:
        print("❌ Could not start server on any available port.")

if __name__ == "__main__":
    start_server()
