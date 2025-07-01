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
    print("🚀 Starting B2B Vault Scraper Web Interface...")
    
    # Check if Flask is installed
    install_flask()
    
    # Create templates directory if it doesn't exist
    os.makedirs("templates", exist_ok=True)
    
    print("🌐 Starting web server...")
    print("📱 Opening in your browser...")
    print("⏹️  Press Ctrl+C to stop the server")
    print("=" * 50)
    print("🔗 Web Interface: http://localhost:5000")
    print("=" * 50)
    
    # Give server time to start
    time.sleep(2)
    
    # Open browser
    webbrowser.open('http://localhost:5000')
    
    # Start the Flask app
    from web_interface import app
    app.run(host='127.0.0.1', port=5000, debug=False)

if __name__ == "__main__":
    start_web_interface()
