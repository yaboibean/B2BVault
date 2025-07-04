#!/usr/bin/env python3
"""
Start the web interface for B2B Vault Scraper
"""
import subprocess
import webbrowser
import time
import os

def install_flask():
    """Install Flask if not already installed"""
    try:
        import flask
        print("✅ Flask is already installed")
    except ImportError:
        print("📦 Installing Flask...")
        subprocess.check_call(["pip", "install", "flask"])
        print("✅ Flask installed successfully")

def start_web_interface():
    """Start the web interface"""
    print("🚀 Starting B2B Vault Scraper Interactive Web Interface...")
    print("💡 NOTE: This runs locally only. For Netlify deployment, use the generated static site.")
    
    # Check if Flask is installed
    install_flask()
    
    print("🌐 Starting interactive web server...")
    print("🔍 Fetching available categories from B2B Vault...")
    print("📱 Opening in your browser...")
    print("⏹️  Press Ctrl+C to stop the server")
    print("=" * 50)
    print("🔗 Web Interface: http://localhost:5001")
    print("💡 Select categories → Start scraping → View results!")
    print("📑 All available B2B Vault categories will be loaded automatically")
    print("🌐 After scraping, visit /generate_static_site to prepare for Netlify")
    print("=" * 50)
    
    # Give server time to start
    time.sleep(2)
    
    # Open browser
    webbrowser.open('http://localhost:5001')
    
    # Start the interactive server
    from interactive_server import app
    app.run(host='127.0.0.1', port=5001, debug=False)

if __name__ == "__main__":
    start_web_interface()
