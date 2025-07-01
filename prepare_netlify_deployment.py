#!/usr/bin/env python3
"""
Script to prepare files for Netlify deployment with tag selection interface
"""
import os
import shutil
import glob
import time

def prepare_netlify_deployment():
    """Prepare all files for Netlify deployment with static tag selector"""
    
    netlify_site_dir = "netlify_site"
    scraped_data_dir = "scraped_data"
    
    print("🚀 Preparing comprehensive Netlify deployment...")
    
    # Create netlify_site directory
    os.makedirs(netlify_site_dir, exist_ok=True)
    
    # 1. Copy the main dashboard (if exists)
    website_dir = os.path.join(scraped_data_dir, "website")
    if os.path.exists(os.path.join(website_dir, "index.html")):
        print("✅ Copying main dashboard...")
        shutil.copy2(os.path.join(website_dir, "index.html"), 
                    os.path.join(netlify_site_dir, "index.html"))
    else:
        print("⚠️  No main dashboard found - creating placeholder...")
        placeholder_html = """
<!DOCTYPE html>
<html>
<head>
    <title>B2B Vault Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
    <h1>B2B Vault Analysis Dashboard</h1>
    <p>No analysis data available yet.</p>
    <p><a href="./scraper.html">Use the scraper tool to generate content</a></p>
</body>
</html>
        """
        with open(os.path.join(netlify_site_dir, "index.html"), "w") as f:
            f.write(placeholder_html)
    
    # 2. Copy PDF files
    if os.path.exists(scraped_data_dir):
        pdf_files = glob.glob(os.path.join(scraped_data_dir, "*comprehensive_report*.pdf"))
        if pdf_files:
            latest_pdf = max(pdf_files, key=os.path.getmtime)
            expected_pdf_name = f"b2b_vault_comprehensive_report_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
            dest_pdf_path = os.path.join(netlify_site_dir, expected_pdf_name)
            
            try:
                shutil.copy2(latest_pdf, dest_pdf_path)
                print(f"✅ Copied PDF: {os.path.basename(latest_pdf)} -> {expected_pdf_name}")
                
                # Update HTML to reference correct PDF
                index_path = os.path.join(netlify_site_dir, "index.html")
                if os.path.exists(index_path):
                    with open(index_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    # Replace PDF references
                    html_content = html_content.replace(
                        "../b2b_vault_comprehensive_report_20250630_161238.pdf",
                        f"./{expected_pdf_name}"
                    )
                    
                    with open(index_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                        
            except Exception as e:
                print(f"❌ Error copying PDF: {e}")
        else:
            print("⚠️  No PDF files found in scraped_data directory")
    
    # 3. Create static tag selector page
    print("✅ Creating static tag selector...")
    
    # Available tags (same as in interactive_server.py)
    available_tags = [
        "All", "Content Marketing", "Demand Generation", "ABM & GTM",
        "Paid Marketing", "Marketing Ops", "Event Marketing", "AI",
        "Product Marketing", "Sales", "General", "Affiliate & Partnerships",
        "Copy & Positioning"
    ]
    
    scraper_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>B2B Vault Scraper - Tag Selection</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        
        .header h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2.5rem;
        }}
        
        .info-box {{
            background: #e8f4f8;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        
        .info-box h3 {{
            color: #2c3e50;
            margin-bottom: 15px;
        }}
        
        .info-box ol {{
            margin-left: 20px;
            color: #555;
        }}
        
        .info-box li {{
            margin-bottom: 8px;
        }}
        
        .tags-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
            margin-bottom: 30px;
        }}
        
        .tag-checkbox {{
            display: none;
        }}
        
        .tag-label {{
            display: block;
            padding: 12px 16px;
            background: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 500;
            font-size: 0.9rem;
        }}
        
        .tag-label:hover {{
            background: #e9ecef;
            transform: translateY(-2px);
        }}
        
        .tag-checkbox:checked + .tag-label {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}
        
        .tag-label.all-tag {{
            background: #27ae60;
            color: white;
            border-color: #27ae60;
            font-weight: bold;
        }}
        
        .tag-checkbox:checked + .tag-label.all-tag {{
            background: #219a52;
            border-color: #219a52;
        }}
        
        .controls {{
            text-align: center;
            margin-bottom: 30px;
        }}
        
        .btn {{
            padding: 15px 30px;
            margin: 0 10px;
            border: none;
            border-radius: 25px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .btn-primary {{
            background: #667eea;
            color: white;
        }}
        
        .btn-primary:hover {{
            background: #5a6fd8;
            transform: translateY(-2px);
        }}
        
        .btn-secondary {{
            background: #95a5a6;
            color: white;
        }}
        
        .command-output {{
            background: #2c3e50;
            color: #ecf0f1;
            padding: 20px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            margin-top: 20px;
            display: none;
        }}
        
        .command-output h3 {{
            color: #ecf0f1;
            margin-bottom: 15px;
        }}
        
        .command-text {{
            background: #34495e;
            padding: 15px;
            border-radius: 5px;
            border: 1px solid #5a6c7d;
            user-select: all;
            cursor: text;
        }}
        
        .navigation {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }}
        
        .nav-link {{
            display: inline-block;
            padding: 10px 20px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 20px;
            margin: 0 10px;
            transition: background 0.3s ease;
        }}
        
        .nav-link:hover {{
            background: #2980b9;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 B2B Vault Scraper</h1>
            <p>Generate scraping commands for local execution</p>
        </div>
        
        <div class="info-box">
            <h3>📋 How to Use (Static Version):</h3>
            <ol>
                <li><strong>Select categories</strong> you want to scrape below</li>
                <li><strong>Click "Generate Command"</strong> to get the Python command</li>
                <li><strong>Copy and run</strong> the command locally on your machine</li>
                <li><strong>Upload results</strong> back to Netlify when scraping is complete</li>
            </ol>
            <p style="margin-top: 15px; padding: 10px; background: #fff3cd; border-radius: 5px; color: #856404;">
                <strong>Note:</strong> This static version generates commands for local execution. 
                The interactive scraper requires a server environment.
            </p>
        </div>
        
        <div class="tag-selection">
            <h2>📑 Select Categories to Scrape:</h2>
            <div class="tags-grid">"""
    
    # Add tag checkboxes
    for i, tag in enumerate(available_tags):
        tag_class = "all-tag" if tag == "All" else ""
        scraper_html += f"""
                <div>
                    <input type="checkbox" id="tag-{i}" class="tag-checkbox" value="{tag}">
                    <label for="tag-{i}" class="tag-label {tag_class}">
                        {"🌟 " + tag if tag == "All" else tag}
                    </label>
                </div>"""
    
    scraper_html += f"""
            </div>
        </div>
        
        <div class="controls">
            <button class="btn btn-secondary" onclick="selectAll()">Select All Categories</button>
            <button class="btn btn-secondary" onclick="clearAll()">Clear Selection</button>
            <button class="btn btn-primary" onclick="generateCommand()">Generate Scraping Command</button>
        </div>
        
        <div class="command-output" id="commandOutput">
            <h3>📋 Copy and run this command locally:</h3>
            <div class="command-text" id="commandText" onclick="selectText(this)">
                Click "Generate Command" first
            </div>
            <p style="margin-top: 15px; color: #bdc3c7; font-size: 0.9rem;">
                💡 Click the command to select it, then copy (Ctrl+C/Cmd+C)
            </p>
        </div>
        
        <div class="navigation">
            <a href="./index.html" class="nav-link">📊 View Analysis Dashboard</a>
            <a href="https://github.com/yourusername/B2BVaultScraper" class="nav-link" target="_blank">📚 Download Scraper</a>
        </div>
    </div>

    <script>
        function selectAll() {{
            const allCheckbox = document.querySelector('input[value="All"]');
            if (allCheckbox) {{
                allCheckbox.checked = true;
            }}
        }}
        
        function clearAll() {{
            const checkboxes = document.querySelectorAll('.tag-checkbox');
            checkboxes.forEach(cb => cb.checked = false);
        }}
        
        function generateCommand() {{
            const selectedTags = Array.from(document.querySelectorAll('.tag-checkbox:checked'))
                .map(cb => cb.value);
            
            if (selectedTags.length === 0) {{
                alert('Please select at least one category');
                return;
            }}
            
            const tagsParam = selectedTags.join(',');
            const command = `python3 B2Bscraper.py --tags="${{tagsParam}}" --generate-netlify`;
            
            document.getElementById('commandText').textContent = command;
            document.getElementById('commandOutput').style.display = 'block';
        }}
        
        function selectText(element) {{
            const range = document.createRange();
            range.selectNodeContents(element);
            const selection = window.getSelection();
            selection.removeAllRanges();
            selection.addRange(range);
        }}
    </script>
</body>
</html>"""
    
    with open(os.path.join(netlify_site_dir, "scraper.html"), "w", encoding="utf-8") as f:
        f.write(scraper_html)
    
    # 4. Create Netlify configuration files
    print("✅ Creating Netlify configuration...")
    
    netlify_toml = """[build]
  publish = "."

[build.environment]
  NODE_VERSION = "18"

[[headers]]
  for = "*.pdf"
  [headers.values]
    Content-Type = "application/pdf"
    Cache-Control = "public, max-age=86400"
    
[[headers]]
  for = "*.html"
  [headers.values]
    Content-Type = "text/html; charset=utf-8"
    Cache-Control = "public, max-age=3600"

[[redirects]]
  from = "/scraper"
  to = "/scraper.html"
  status = 301

[[redirects]]
  from = "/dashboard"
  to = "/index.html"
  status = 301
"""
    
    with open(os.path.join(netlify_site_dir, "netlify.toml"), "w") as f:
        f.write(netlify_toml)
    
    redirects_content = """# Netlify redirects
/scraper /scraper.html 301
/dashboard /index.html 301
/api/* /404.html 404
/* /index.html 200
"""
    with open(os.path.join(netlify_site_dir, "_redirects"), "w") as f:
        f.write(redirects_content)
    
    # 5. Create deployment README
    print("✅ Creating deployment documentation...")
    
    readme_content = f"""# B2B Vault Analysis Dashboard - Netlify Deployment

## 🌐 Live Features
- **Main Dashboard**: [index.html](./index.html) - View analyzed articles
- **Scraper Tool**: [scraper.html](./scraper.html) - Generate scraping commands
- **PDF Report**: Download comprehensive analysis report

## 🚀 Quick Deploy to Netlify
1. **Upload Files**: Drag the entire `{netlify_site_dir}` folder to Netlify
2. **Configure**: Set publish directory to root (`.`)
3. **Deploy**: Your site will be live immediately!

## 🔧 How to Update Content

### Method 1: Use Static Scraper (Recommended)
1. Visit `/scraper.html` on your deployed site
2. Select categories and generate command
3. Run command locally: `python3 B2Bscraper.py --tags="Sales,Marketing" --generate-netlify`
4. Re-upload the generated files

### Method 2: Local Development
```bash
# Clone the repository
git clone [your-repo-url]
cd B2BVaultScraper

# Install dependencies
pip install playwright beautifulsoup4 flask requests tenacity weasyprint

# Run scraper
python3 B2Bscraper.py --tags="Sales,Marketing,AI"

# Prepare for Netlify
python3 prepare_netlify_deployment.py

# Upload netlify_site folder to Netlify
```

## 📁 File Structure
```
netlify_site/
├── index.html              # Main dashboard
├── scraper.html            # Static tag selector
├── *.pdf                   # Analysis reports
├── netlify.toml           # Netlify configuration
├── _redirects             # URL redirects
└── README.md              # This file
```

## 🎯 Supported Categories
{', '.join(available_tags)}

## 📊 Features
- ✅ **Responsive Design**: Works on desktop and mobile
- ✅ **Search Functionality**: Find articles quickly
- ✅ **PDF Downloads**: Complete analysis reports
- ✅ **SEO Optimized**: Meta tags and proper structure
- ✅ **Fast Loading**: Optimized static files

## 🔗 Useful Links
- Dashboard: `/` or `/dashboard`
- Scraper: `/scraper`
- PDF Report: `/*.pdf`

---
Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}
Deployment ready! 🚀
"""
    
    with open(os.path.join(netlify_site_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    # 6. List all files for deployment
    print("\n📁 Netlify deployment files ready:")
    files = os.listdir(netlify_site_dir)
    for file in files:
        file_path = os.path.join(netlify_site_dir, file)
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            print(f"   ✅ {file} ({size:,} bytes)")
    
    print(f"\n🌐 Ready for Netlify deployment!")
    print(f"📁 Upload the contents of '{netlify_site_dir}' to Netlify")
    print("💡 Set publish directory to '.' (root)")
    print("🚀 Your static B2B Vault dashboard will be live!")
    
    return True

if __name__ == "__main__":
    prepare_netlify_deployment()
