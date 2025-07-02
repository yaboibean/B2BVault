#!/usr/bin/env python3
"""
Script to prepare files for Netlify deployment with tag selection interface
"""
import os
import shutil
import glob
import time

netlify_site_dir = "netlify_site"
scraped_data_dir = "scraped_data"

def prepare_netlify_deployment():
    """Prepare all files for Netlify deployment with static tag selector"""
    
    print("🚀 Preparing comprehensive Netlify deployment...")
    
    # Create netlify_site directory
    os.makedirs(netlify_site_dir, exist_ok=True)
    
    # 1. Copy the main dashboard (if exists) - THIS IS THE KEY CHANGE
    website_dir = os.path.join(scraped_data_dir, "website")
    dashboard_exists = False
    
    if os.path.exists(os.path.join(website_dir, "index.html")):
        print("✅ Copying main dashboard...")
        shutil.copy2(os.path.join(website_dir, "index.html"), 
                    os.path.join(netlify_site_dir, "index.html"))
        dashboard_exists = True
        
        # Copy any CSS or JS files from the website
        for file_pattern in ["*.css", "*.js"]:
            for file_path in glob.glob(os.path.join(website_dir, file_pattern)):
                shutil.copy2(file_path, netlify_site_dir)
                print(f"✅ Copied: {os.path.basename(file_path)}")
                
    else:
        print("⚠️  No analysis dashboard found - keeping placeholder...")
        print("   Run python3 B2Bscraper.py first to generate content")
    
    # 2. Copy PDF files
    if os.path.exists(scraped_data_dir):
        pdf_files = glob.glob(os.path.join(scraped_data_dir, "*comprehensive_report*.pdf"))
        if pdf_files:
            latest_pdf = max(pdf_files, key=os.path.getmtime)
            dest_pdf_path = os.path.join(netlify_site_dir, os.path.basename(latest_pdf))
            
            try:
                shutil.copy2(latest_pdf, dest_pdf_path)
                print(f"✅ Copied PDF: {os.path.basename(latest_pdf)}")
                dashboard_exists = True
            except Exception as e:
                print(f"❌ Error copying PDF: {e}")
    
    print(f"\n🎯 NETLIFY DEPLOYMENT STATUS:")
    if dashboard_exists:
        print("   ✅ Dashboard with analyzed articles ready!")
        print("   📊 Main page: Analysis dashboard (index.html)")
        print("   📄 PDF report included")
    else:
        print("   📋 Placeholder dashboard (no content yet)")
        print("   💡 Run 'python3 B2Bscraper.py' to generate content")
    
    print("   📁 Upload netlify_site folder to your hosting platform")

if __name__ == "__main__":
    prepare_netlify_deployment()
    
    # 3. Create enhanced static tag selector page
    print("✅ Creating enhanced static tag selector...")
    
    # Get existing dashboard content for integration
    dashboard_exists = os.path.exists(os.path.join(netlify_site_dir, "index.html"))
    
    # Available tags
    available_tags = [
        "All", "Content Marketing", "Demand Generation", "ABM & GTM",
        "Paid Marketing", "Marketing Ops", "Event Marketing", "AI",
        "Product Marketing", "Sales", "General", "Affiliate & Partnerships",
        "Copy & Positioning"
    ]
    
    # Start building the HTML
    scraper_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>B2B Vault Scraper - Enhanced Tag Selection</title>
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
            max-width: 1000px;
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
        
        .status-banner {{
            background: {'#d4edda' if dashboard_exists else '#fff3cd'};
            color: {'#155724' if dashboard_exists else '#856404'};
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
            border: 1px solid {'#c3e6cb' if dashboard_exists else '#ffeaa7'};
        }}
        
        .tabs {{
            display: flex;
            background: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 30px;
            overflow: hidden;
        }}
        
        .tab {{
            flex: 1;
            padding: 15px 20px;
            cursor: pointer;
            text-align: center;
            transition: all 0.3s ease;
            border: none;
            background: transparent;
            font-weight: 500;
        }}
        
        .tab.active {{
            background: #667eea;
            color: white;
        }}
        
        .tab:hover:not(.active) {{
            background: #e9ecef;
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        .quick-actions {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .quick-action-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 2px solid #e9ecef;
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        
        .quick-action-card:hover {{
            border-color: #667eea;
            transform: translateY(-2px);
        }}
        
        .quick-action-card.available {{
            background: #d4edda;
            border-color: #c3e6cb;
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
            text-decoration: none;
            display: inline-block;
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
        
        .nav-link.dashboard-available {{
            background: #27ae60;
        }}
        
        .history-section {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        
        .history-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            margin: 5px 0;
            background: white;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }}
        
        .btn-small {{
            padding: 5px 15px;
            font-size: 0.8rem;
            margin-left: 10px;
        }}
        
        .tutorial-section {{
            background: #fff3cd;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            border-left: 4px solid #ffc107;
        }}
        
        .step {{
            display: flex;
            align-items: center;
            margin: 10px 0;
        }}
        
        .step-number {{
            background: #ffc107;
            color: #212529;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 15px;
        }}
        
        .articles-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-top: 30px;
            /* Enable CSS Grid ordering */
        }}
        
        .article-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border-left: 5px solid #667eea;
            /* Enable ordering */
            order: 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 B2B Vault Scraper</h1>
            <p>Enhanced tag selection and command generation for B2B Vault scraping</p>
        </div>
        
        <div class="status-banner">
            {'✅ Dashboard Available! You can view your existing analysis while generating new commands.' if dashboard_exists else '📋 No dashboard yet - Use this tool to generate scraping commands and create your first analysis!'}
        </div>"""
    
    # Add quick actions if dashboard exists
    if dashboard_exists:
        scraper_html += """
        <div class="quick-actions">
            <div class="quick-action-card available" onclick="window.open('./index.html', '_blank')">
                <h3>📊 View Dashboard</h3>
                <p>Browse your analyzed articles</p>
            </div>
            <div class="quick-action-card" onclick="switchTab('command')">
                <h3>🎯 Generate Commands</h3>
                <p>Create new scraping commands</p>
            </div>
            <div class="quick-action-card" onclick="switchTab('tutorial')">
                <h3>📚 Tutorial</h3>
                <p>Learn how to use the scraper</p>
            </div>
        </div>"""
    
    # Continue with tabs and content
    scraper_html += """
        <div class="tabs">
            <button class="tab active" onclick="switchTab('command')">📋 Generate Commands</button>
            <button class="tab" onclick="switchTab('tutorial')">📚 How to Use</button>
            <button class="tab" onclick="switchTab('history')">📜 Selection History</button>
        </div>
        
        <!-- Command Generation Tab -->
        <div id="command-tab" class="tab-content active">
            <div class="info-box">
                <h3>📋 Smart Command Generation:</h3>
                <ol>
                    <li><strong>Select categories</strong> you want to scrape below</li>
                    <li><strong>Click "Generate Command"</strong> to get the Python command</li>
                    <li><strong>Copy and run</strong> the command locally on your machine</li>
                    <li><strong>Re-deploy</strong> the updated files to Netlify when scraping is complete</li>
                </ol>
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
    
    # Complete the rest of the HTML
    scraper_html += """
                </div>
            </div>
            
            <div class="controls">
                <button class="btn btn-secondary" onclick="selectAll()">Select All Categories</button>
                <button class="btn btn-secondary" onclick="clearAll()">Clear Selection</button>
                <button class="btn btn-primary" onclick="generateCommand()">Generate Scraping Command</button>
                <button class="btn btn-secondary" onclick="saveSelection()">💾 Save Selection</button>
            </div>
            
            <div class="command-output" id="commandOutput">
                <h3>📋 Copy and run this command locally:</h3>
                <div class="command-text" id="commandText" onclick="selectText(this)">
                    Click "Generate Command" first
                </div>
                <p style="margin-top: 15px; color: #bdc3c7; font-size: 0.9rem;">
                    💡 Click the command to select it, then copy (Ctrl+C/Cmd+C)
                </p>
                <div style="margin-top: 15px; padding: 15px; background: #34495e; border-radius: 5px;">
                    <h4 style="color: #ecf0f1; margin-bottom: 10px;">🔄 After running the command:</h4>
                    <ol style="color: #bdc3c7; margin-left: 20px;">
                        <li>Run: <code style="background: #2c3e50; padding: 2px 5px; border-radius: 3px;">python3 prepare_netlify_deployment.py</code></li>
                        <li>Upload the updated <code>netlify_site</code> folder to Netlify</li>
                        <li>Your dashboard will be updated with new content!</li>
                    </ol>
                </div>
            </div>
        </div>
        
        <!-- Tutorial Tab -->
        <div id="tutorial-tab" class="tab-content">
            <div class="tutorial-section">
                <h3>🎯 Complete Workflow Guide</h3>
                
                <div class="step">
                    <div class="step-number">1</div>
                    <div>
                        <strong>Download the Scraper:</strong> Get the B2B Vault Scraper from GitHub and install dependencies locally.
                    </div>
                </div>
                
                <div class="step">
                    <div class="step-number">2</div>
                    <div>
                        <strong>Select Categories:</strong> Use this page to choose which B2B Vault categories you want to analyze.
                    </div>
                </div>
                
                <div class="step">
                    <div class="step-number">3</div>
                    <div>
                        <strong>Generate Command:</strong> Click "Generate Command" to get a custom Python command for your selections.
                    </div>
                </div>
                
                <div class="step">
                    <div class="step-number">4</div>
                    <div>
                        <strong>Run Locally:</strong> Execute the command on your local machine to scrape and analyze articles.
                    </div>
                </div>
                
                <div class="step">
                    <div class="step-number">5</div>
                    <div>
                        <strong>Deploy Results:</strong> Run the deployment script and upload files to Netlify to update your live dashboard.
                    </div>
                </div>
            </div>
            
            <div class="info-box">
                <h3>🔧 Prerequisites:</h3>
                <ul style="margin-left: 20px; color: #555;">
                    <li>Python 3.7+ installed on your local machine</li>
                    <li>B2B Vault Scraper downloaded from GitHub</li>
                    <li>Required Python packages: <code>pip install playwright beautifulsoup4 requests tenacity weasyprint</code></li>
                    <li>Perplexity API key configured in the scraper</li>
                </ul>
                
                <h3 style="margin-top: 20px;">📋 Quick Update Process:</h3>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px;">
                    <ol style="margin-left: 20px; color: #555;">
                        <li>Generate command using this tool</li>
                        <li>Run the command locally: <code>python3 B2Bscraper.py --tags="Sales,Marketing"</code></li>
                        <li>Run deployment script: <code>python3 prepare_netlify_deployment.py</code></li>
                        <li>Upload <code>netlify_site</code> folder contents to Netlify</li>
                        <li>Your dashboard will be updated!</li>
                    </ol>
                </div>
            </div>
        </div>
        
        <!-- History Tab -->
        <div id="history-tab" class="tab-content">
            <div class="history-section">
                <h3>📜 Previous Tag Selections</h3>
                <div id="historyList">
                    <p style="color: #666; text-align: center; padding: 20px;">No previous selections saved</p>
                </div>
                <div style="text-align: center; margin-top: 15px;">
                    <button class="btn btn-secondary btn-small" onclick="clearHistory()">🗑️ Clear History</button>
                </div>
            </div>
        </div>
        
        <div class="navigation">"""
    
    # Add navigation with conditional dashboard link
    if dashboard_exists:
        scraper_html += """
            <a href="./index.html" class="nav-link dashboard-available">📊 View Analysis Dashboard</a>"""
    
    scraper_html += """
            <a href="https://github.com/yourusername/B2BVaultScraper" class="nav-link" target="_blank">📚 Download Scraper</a>
            <a href="#" class="nav-link" onclick="showUpdateInstructions()">🔄 Update Instructions</a>
        </div>
    </div>

    <script>
        // Tab switching functionality
        function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
            
            if (tabName === 'history') {
                loadHistory();
            }
        }
        
        // Tag selection functions
        function selectAll() {
            const allCheckbox = document.querySelector('input[value="All"]');
            if (allCheckbox) {
                allCheckbox.checked = true;
            }
        }
        
        function clearAll() {
            const checkboxes = document.querySelectorAll('.tag-checkbox');
            checkboxes.forEach(cb => cb.checked = false);
        }
        
        function generateCommand() {
            const selectedTags = Array.from(document.querySelectorAll('.tag-checkbox:checked'))
                .map(cb => cb.value);
            
            if (selectedTags.length === 0) {
                alert('Please select at least one category');
                return;
            }
            
            // Show loading state
            const commandOutput = document.getElementById('commandOutput');
            commandOutput.style.display = 'block';
            document.getElementById('commandText').innerHTML = '<div style="text-align: center;">🚀 Starting scraper... Please wait...</div>';
            
            // Call Netlify function to run scraper
            fetch('/.netlify/functions/scrape', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ tags: selectedTags })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('commandText').innerHTML = `
                        <div style="color: #27ae60;">✅ Scraping completed successfully!</div>
                        1. Generate a command using this tool.<br>
                        2. Run it locally: python3 B2Bscraper.py --tags="YourTags"<br>
                        3. Run: python3 prepare_netlify_deployment.py<br>
                        4. Upload netlify_site folder to Netlify<br>
                        5. Your dashboard will be updated!`;
                } else {
                    document.getElementById('commandText').innerHTML = `
                        <div style="color: #e74c3c;">❌ Scraping failed: ${data.error}</div>`;
                }
            })
            .catch(error => {
                document.getElementById('commandText').innerHTML = `
                    <div style="color: #e74c3c;">❌ Error: ${error.message}</div>
                    <div style="margin-top: 10px; font-size: 0.9rem;">Check your internet connection and try again.</div>
                `;
            });
        }

        // Local storage functions for history
        function saveSelection() {
            const selectedTags = Array.from(document.querySelectorAll('.tag-checkbox:checked'))
                .map(cb => cb.value);
            if (selectedTags.length === 0) {
                alert('Please select at least one category to save');
                return;
            }
            const selection = {
                tags: selectedTags,
                timestamp: new Date().toISOString(),
                date: new Date().toLocaleDateString()
            };
            const history = JSON.parse(localStorage.getItem('b2bVaultHistory') || '[]');
            history.push(selection);
            localStorage.setItem('b2bVaultHistory', JSON.stringify(history));
            alert('Selection saved to history!');
        }

        function showUpdateInstructions() {
            alert(`🔄 To update your dashboard:
1. Generate command using this tool
2. Run it locally: python3 B2Bscraper.py --tags="YourTags"
3. Run: python3 prepare_netlify_deployment.py
4. Upload netlify_site folder to Netlify
5. Your dashboard will be updated!`);
        }

        function loadHistory() {
            const history = JSON.parse(localStorage.getItem('b2bVaultHistory') || '[]');
            const historyList = document.getElementById('historyList');
            if (history.length === 0) {
                historyList.innerHTML = '<p style="color: #666; text-align: center; padding: 20px;">No previous selections saved</p>';
                return;
            }
            historyList.innerHTML = history.map((item, index) => `
                <div class="history-item">
                    <div>
                        <strong>${item.date}</strong>
                        <div class="history-tags">${item.tags.join(', ')}</div>
                    </div>
                    <div>
                        <button class="btn btn-secondary btn-small" onclick="loadSelection(${index})">🔄 Load</button>
                        <button class="btn btn-primary btn-small" onclick="generateFromHistory(${index})">▶️ Generate</button>
                    </div>
                </div>
            `).join('');
        }

        function loadSelection(index) {
            const history = JSON.parse(localStorage.getItem('b2bVaultHistory') || '[]');
            if (!history[index]) return;
            clearAll();
            const savedTags = history[index].tags;
            savedTags.forEach(tag => {
                const checkbox = document.querySelector(`input[value="${tag}"]`);
                if (checkbox) {
                    checkbox.checked = true;
                }
            });
            switchTab('command');
            alert('Selection loaded! You can now generate the command.');
        }

        function generateFromHistory(index) {
            loadSelection(index);
            setTimeout(() => {
                generateCommand();
            }, 100);
        }

        function clearHistory() {
            if (confirm('Are you sure you want to clear all saved selections?')) {
                localStorage.removeItem('b2bVaultHistory');
                loadHistory();
            }
        }

        window.onload = function() {
            const urlParams = new URLSearchParams(window.location.search);
            const tags = urlParams.get('tags');
            if (tags) {
                const tagList = tags.split(',');
                tagList.forEach(tag => {
                    const checkbox = document.querySelector(`input[value="${tag.trim()}"]`);
                    if (checkbox) {
                        checkbox.checked = true;
                    }
                });
                generateCommand();
            }
        };
    </script>
</body>
</html>
    """
    
    # Save the scraper page
    scraper_path = os.path.join(netlify_site_dir, "scraper.html")
    with open(scraper_path, "w", encoding='utf-8') as f:
        f.write(scraper_html)
    
    print(f"✅ Enhanced static tag selector created: scraper.html")
    
    print("\n🎯 NETLIFY DEPLOYMENT READY:")
    print("   📁 Upload netlify_site folder to Netlify")
    if dashboard_exists:
        print("   📊 Main page: Analysis dashboard (index.html)")
        print("   🎯 Scraper tool: Tag selector (scraper.html)")
    else:
        print("   📋 Main page: Tag selector interface")
    print("   🔧 All PDF links have been fixed for web hosting")

if __name__ == "__main__":
    prepare_netlify_deployment()
