#!/usr/bin/env python3
"""
Script to prepare files for Netlify deployment
"""
import os
import shutil
import glob

def prepare_netlify_deployment():
    """Prepare all files for Netlify deployment"""
    
    netlify_site_dir = "netlify_site"
    scraped_data_dir = "scraped_data"
    
    print("🚀 Preparing Netlify deployment...")
    
    # Create netlify_site directory if it doesn't exist
    os.makedirs(netlify_site_dir, exist_ok=True)
    
    # 1. Copy the latest PDF to netlify_site with the expected name
    if os.path.exists(scraped_data_dir):
        pdf_files = glob.glob(os.path.join(scraped_data_dir, "*comprehensive_report*.pdf"))
        if pdf_files:
            latest_pdf = max(pdf_files, key=os.path.getmtime)
            expected_pdf_name = "b2b_vault_comprehensive_report_20250630_161238.pdf"
            dest_pdf_path = os.path.join(netlify_site_dir, expected_pdf_name)
            
            try:
                shutil.copy2(latest_pdf, dest_pdf_path)
                print(f"✅ Copied PDF: {os.path.basename(latest_pdf)} -> {expected_pdf_name}")
            except Exception as e:
                print(f"❌ Error copying PDF: {e}")
        else:
            print("⚠️  No PDF files found in scraped_data directory")
    else:
        print("⚠️  scraped_data directory not found")
    
    # 2. Verify index.html exists
    index_path = os.path.join(netlify_site_dir, "index.html")
    if os.path.exists(index_path):
        print("✅ index.html found")
    else:
        print("❌ index.html not found - you need to generate the website first")
        return False
    
    # 3. Create a simple netlify.toml for deployment settings
    netlify_toml_content = """# Netlify configuration file
[build]
  # This is where our built files will be
  publish = "."
  
[build.environment]
  # Environment variables (if needed)
  
[[headers]]
  # Set headers for PDF files
  for = "*.pdf"
  [headers.values]
    Content-Type = "application/pdf"
    Content-Disposition = "inline"

[[headers]]
  # Set headers for HTML files
  for = "*.html"
  [headers.values]
    Content-Type = "text/html; charset=utf-8"

# Redirect rules (if needed)
[[redirects]]
  from = "/pdf"
  to = "/b2b_vault_comprehensive_report_20250630_161238.pdf"
  status = 302
"""
    
    netlify_toml_path = os.path.join(netlify_site_dir, "netlify.toml")
    with open(netlify_toml_path, "w") as f:
        f.write(netlify_toml_content)
    print("✅ Created netlify.toml configuration")
    
    # 4. Create a README for deployment
    readme_content = """# B2B Vault Analysis Dashboard

This is a static website generated from B2B Vault article analysis.

## Files included:
- `index.html` - Main dashboard
- `b2b_vault_comprehensive_report_20250630_161238.pdf` - Complete analysis report
- `netlify.toml` - Netlify configuration

## To deploy:
1. Upload all files in this directory to Netlify
2. Set publish directory to root (.)
3. The PDF download link should work automatically

Generated on: """ + os.popen('date').read().strip()
    
    readme_path = os.path.join(netlify_site_dir, "README.md")
    with open(readme_path, "w") as f:
        f.write(readme_content)
    print("✅ Created README.md")
    
    # 5. List all files that will be deployed
    print("\n📁 Files ready for Netlify deployment:")
    for file in os.listdir(netlify_site_dir):
        file_path = os.path.join(netlify_site_dir, file)
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            print(f"   {file} ({size:,} bytes)")
    
    print(f"\n🌐 Ready to deploy! Upload the contents of '{netlify_site_dir}' to Netlify.")
    print("💡 Make sure to set the publish directory to '.' (root) in Netlify settings.")
    
    return True

if __name__ == "__main__":
    prepare_netlify_deployment()
