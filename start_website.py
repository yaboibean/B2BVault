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
import shutil
import glob

def fix_pdf_link():
    """Find and copy the PDF file to netlify_site if needed"""
    scraped_data_dir = "scraped_data"
    netlify_site_dir = "netlify_site"
    expected_pdf = "b2b_vault_comprehensive_report_20250630_161238.pdf"
    dest_path = os.path.join(netlify_site_dir, expected_pdf)
    
    # Check if PDF already exists in netlify_site
    if os.path.exists(dest_path):
        print(f"✅ PDF file already exists: {expected_pdf}")
        return True
    
    # Look for any comprehensive report PDF in scraped_data
    if os.path.exists(scraped_data_dir):
        pdf_files = glob.glob(os.path.join(scraped_data_dir, "*comprehensive_report*.pdf"))
        if pdf_files:
            latest_pdf = max(pdf_files, key=os.path.getmtime)
            try:
                # Create netlify_site directory if it doesn't exist
                os.makedirs(netlify_site_dir, exist_ok=True)
                shutil.copy2(latest_pdf, dest_path)
                print(f"📄 Copied PDF: {os.path.basename(latest_pdf)} -> {expected_pdf}")
                return True
            except Exception as e:
                print(f"⚠️  Could not copy PDF: {e}")
        else:
            print(f"⚠️  No comprehensive report PDF found in {scraped_data_dir}")
    else:
        print(f"⚠️  {scraped_data_dir} directory not found")
    
    return False

def start_server():
    # Always use netlify_site as the website directory
    website_dir = "netlify_site"
    
    if not os.path.exists(website_dir):
        print(f"❌ Website directory '{website_dir}' not found.")
        print("Please make sure the netlify_site directory exists with index.html")
        return
    
    if not os.path.exists(os.path.join(website_dir, "index.html")):
        print(f"❌ index.html not found in {website_dir}")
        return
    
    # Try to fix PDF link
    print("🔧 Checking PDF file...")
    fix_pdf_link()
    
    # Change to the website directory
    original_dir = os.getcwd()
    
    try:
        os.chdir(website_dir)
        
        # Try different ports if 8000 is busy
        ports_to_try = [8000, 8001, 8002, 8003, 8080]
        
        for PORT in ports_to_try:
            try:
                Handler = http.server.SimpleHTTPRequestHandler
                
                with socketserver.TCPServer(("", PORT), Handler) as httpd:
                    print(f"🌐 B2B Vault Analysis Website")
                    print(f"🚀 Server running at http://localhost:{PORT}")
                    print(f"📁 Serving files from: {os.path.abspath('.')}")
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
            
    finally:
        # Always return to original directory
        os.chdir(original_dir)

if __name__ == "__main__":
    start_server()
