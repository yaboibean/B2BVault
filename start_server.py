#!/usr/bin/env python3
import os
import http.server
import socketserver
import webbrowser
import time
import shutil
import glob

def fix_pdf_link():
    """Find and copy the PDF file to website directory if needed"""
    scraped_data_dir = "scraped_data"
    website_dir = "scraped_data/website"
    
    # Look for any comprehensive report PDF in scraped_data
    if os.path.exists(scraped_data_dir):
        pdf_files = glob.glob(os.path.join(scraped_data_dir, "*comprehensive_report*.pdf"))
        if pdf_files:
            latest_pdf = max(pdf_files, key=os.path.getmtime)
            
            # Copy to website directory with a generic name
            if os.path.exists(website_dir):
                dest_path = os.path.join(website_dir, os.path.basename(latest_pdf))
                if not os.path.exists(dest_path):
                    try:
                        shutil.copy2(latest_pdf, dest_path)
                        print(f"📄 Copied PDF to website directory: {os.path.basename(latest_pdf)}")
                    except Exception as e:
                        print(f"⚠️  Could not copy PDF: {e}")
                return True
    return False

def start_server():
    website_dir = "scraped_data/website"
    PORT = 8000
    
    if not os.path.exists(website_dir):
        print("❌ Website directory not found!")
        print("Please run the scraper first: python3 B2Bscraper.py")
        return
    
    # Try to fix PDF link
    print("🔧 Checking PDF file...")
    fix_pdf_link()
    
    # Change to website directory
    original_dir = os.getcwd()
    
    try:
        os.chdir(website_dir)
        Handler = http.server.SimpleHTTPRequestHandler
        
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"🌐 B2B Vault Analysis Website")
            print(f"🚀 Server running at http://localhost:{PORT}")
            print(f"📁 Serving from: {os.path.abspath('.')}")
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
    finally:
        os.chdir(original_dir)

if __name__ == "__main__":
    start_server()
