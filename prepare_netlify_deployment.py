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
                    
                    # Replace PDF references - fix the path to be in same directory
                    html_content = html_content.replace(
                        "../b2b_vault_comprehensive_report_20250630_161238.pdf",
                        f"./{expected_pdf_name}"
                    )
                    # Also replace any other PDF references that might be using relative paths
                    html_content = html_content.replace(
                        "../b2b_vault_comprehensive_report",
                        f"./b2b_vault_comprehensive_report"
                    )
                    
                    with open(index_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                        
            except Exception as e:
                print(f"❌ Error copying PDF: {e}")
        else:
            print("⚠️  No PDF files found in scraped_data directory")
    
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

        // Advanced fuzzy search functionality
        function fuzzySearch(searchTerm, text) {
            // Convert to lowercase for case-insensitive search
            const query = searchTerm.toLowerCase();
            const target = text.toLowerCase();
            
            // Exact match gets highest score
            if (target.includes(query)) {
                return 100;
            }
            
            // Handle common typos and variations
            const correctedQuery = autoCorrect(query);
            if (correctedQuery !== query && target.includes(correctedQuery)) {
                return 90;
            }
            
            // Split search into words for partial matching
            const queryWords = query.split(/\s+/).filter(word => word.length > 1);
            let score = 0;
            let matches = 0;
            
            queryWords.forEach(word => {
                if (target.includes(word)) {
                    matches++;
                    score += 20;
                } else {
                    // Check for partial word matches
                    const partialMatch = findPartialMatch(word, target);
                    if (partialMatch > 0.7) {
                        matches++;
                        score += partialMatch * 15;
                    }
                }
            });
            
            // Bonus for matching multiple words
            if (matches > 1) {
                score += matches * 5;
            }
            
            return score;
        }
        
        function autoCorrect(word) {
            const corrections = {
                'markting': 'marketing',
                'marketng': 'marketing',
                'marekting': 'marketing',
                'sales': 'sales',
                'slaes': 'sales',
                'leadgen': 'lead generation',
                'lead gen': 'lead generation',
                'ai': 'ai',
                'artifiical': 'artificial',
                'intellgence': 'intelligence',
                'prospectng': 'prospecting',
                'outbound': 'outbound',
                'inbound': 'inbound',
                'convrsion': 'conversion',
                'converion': 'conversion',
                'b2b': 'b2b',
                'saas': 'saas',
                'crm': 'crm',
                'pipeline': 'pipeline',
                'lead': 'lead',
                'prospect': 'prospect',
                'revenue': 'revenue',
                'growth': 'growth',
                'stratgey': 'strategy',
                'strategy': 'strategy'
            };
            
            return corrections[word] || word;
        }
        
        function findPartialMatch(word, text) {
            if (word.length < 3) return 0;
            
            // Check for substring matches
            for (let i = 0; i <= text.length - word.length; i++) {
                const substring = text.substring(i, i + word.length);
                const similarity = calculateSimilarity(word, substring);
                if (similarity > 0.7) return similarity;
            }
            
            return 0;
        }
        
        function calculateSimilarity(str1, str2) {
            const longer = str1.length > str2.length ? str1 : str2;
            const shorter = str1.length > str2.length ? str2 : str1;
            
            if (longer.length === 0) return 1.0;
            
            const editDistance = getEditDistance(longer, shorter);
            return (longer.length - editDistance) / longer.length;
        }
        
        function getEditDistance(str1, str2) {
            const matrix = [];
            
            for (let i = 0; i <= str2.length; i++) {
                matrix[i] = [i];
            }
            
            for (let j = 0; j <= str1.length; j++) {
                matrix[0][j] = j;
            }
            
            for (let i = 1; i <= str2.length; i++) {
                for (let j = 1; j <= str1.length; j++) {
                    if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
                        matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j - 1] + 1,
                        matrix[i][j - 1] + 1,
                        matrix[i - 1][j] + 1
                    );
                }
            }
        }
        
        return matrix[str2.length][str1.length];
    }
    
    function searchArticles() {
        const searchTerm = document.querySelector('.search-input').value.trim();
        const articles = document.querySelectorAll('.article-card');
        const articlesGrid = document.getElementById('articles-grid');
        
        if (searchTerm.length === 0) {
            // Show all articles in original order
            articles.forEach((article, index) => {
                article.style.display = 'block';
                article.style.order = index;
            });
            return;
        }
        
        const searchResults = [];
        
        articles.forEach((article, index) => {
            const title = article.querySelector('.article-title').textContent;
            const content = article.textContent;
            const publisher = article.querySelector('.publisher')?.textContent || '';
            const tabBadge = article.querySelector('.tab-badge')?.textContent || '';
            
            // Calculate relevance scores
            const titleScore = fuzzySearch(searchTerm, title) * 3; // Weight title higher
            const publisherScore = fuzzySearch(searchTerm, publisher) * 2;
            const tabScore = fuzzySearch(searchTerm, tabBadge) * 2;
            const contentScore = fuzzySearch(searchTerm, content);
            
            const totalScore = titleScore + publisherScore + tabScore + contentScore;
            
            searchResults.push({
                element: article,
                score: totalScore,
                originalIndex: index
            });
        });
        
        // Sort by relevance score (highest to lowest)
        searchResults.sort((a, b) => b.score - a.score);
        
        // Apply ordering and visibility
        const threshold = 10; // Minimum score to show
        let visibleCount = 0;
        let displayOrder = 0;
        
        searchResults.forEach((result) => {
            if (result.score >= threshold) {
                result.element.style.display = 'block';
                result.element.style.order = displayOrder;
                displayOrder++;
                visibleCount++;
                
                // Highlight search terms in title
                highlightSearchTerms(result.element, searchTerm);
                
                // Add relevance indicator for high scores
                if (result.score > 50) {
                    result.element.style.borderLeftColor = '#27ae60'; // Green for highly relevant
                } else if (result.score > 25) {
                    result.element.style.borderLeftColor = '#f39c12'; // Orange for moderately relevant
                } else {
                    result.element.style.borderLeftColor = '#667eea'; // Default blue
                }
            } else {
                result.element.style.display = 'none';
            }
        });
        
        // Show search suggestions if no results
        showSearchSuggestions(searchTerm, visibleCount);
        
        // Add search results summary
        showSearchSummary(searchTerm, visibleCount, searchResults.length);
    }
    
    function showSearchSummary(searchTerm, visibleCount, totalCount) {
        let summaryDiv = document.getElementById('search-summary');
        
        if (!summaryDiv) {
            summaryDiv = document.createElement('div');
            summaryDiv.id = 'search-summary';
            summaryDiv.style.cssText = `
                background: #f8f9fa;
                padding: 10px 20px;
                border-radius: 10px;
                margin: 10px 0;
                text-align: center;
                font-size: 0.9rem;
                color: #666;
                border-left: 4px solid #667eea;
            `;
            document.querySelector('.articles-grid').parentNode.insertBefore(
                summaryDiv, 
                document.querySelector('.articles-grid')
            );
        }
        
        if (searchTerm.length > 0) {
            summaryDiv.style.display = 'block';
            if (visibleCount > 0) {
                summaryDiv.innerHTML = `
                    🔍 Found <strong>${visibleCount}</strong> relevant articles for "<strong>${searchTerm}</strong>" 
                    (${totalCount - visibleCount} others filtered out) • Sorted by relevance
                `;
            } else {
                summaryDiv.innerHTML = `
                    🔍 No articles found for "<strong>${searchTerm}</strong>" • Try different keywords
                `;
            }
        } else {
            summaryDiv.style.display = 'none';
        }
    }

        // Real-time search functionality
        let searchTimeout;
        function setupRealTimeSearch() {
            const searchInput = document.querySelector('.search-input');
            
            searchInput.addEventListener('input', function() {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    searchArticles();
                }, 300); // Wait 300ms after user stops typing
            });
            
            // Clear search on Escape key
            searchInput.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    this.value = '';
                    searchArticles();
                }
            });
        }
        
        // Initialize when page loads
        window.onload = function() {
            setupRealTimeSearch();
            
            const urlParams = new URLSearchParams(window.location.search);
            const tags = urlParams.get('tags');
            if (tags) {
                const tagList = tags.split(',');
                tagList.forEach(tag => {
                    const checkbox = document.querySelector(`input[value="${tag.trim()}"]`);
                                    if
                                }
                            };
                        </script>
                    </body>
                    </html>
                    """
