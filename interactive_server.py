#!/usr/bin/env python3
"""
Interactive web interface for B2B Vault Scraper with tag selection
"""
from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import os
import threading
import time
from B2Bscraper import B2BVaultAgent
from playwright.sync_api import sync_playwright
import json

app = Flask(__name__)

# Global variables to track scraping status
scraping_status = {
    'is_running': False,
    'progress': 0,
    'current_step': '',
    'results': None,
    'error': None,
    'log_messages': []
}

# Available tags from B2B Vault - will be dynamically fetched
AVAILABLE_TAGS = [
    "All",
    "Content Marketing", 
    "Demand Generation",
    "ABM & GTM",
    "Paid Marketing",
    "Marketing Ops",
    "Event Marketing",
    "AI",
    "Product Marketing",
    "Sales",
    "General",
    "Affiliate & Partnerships",
    "Copy & Positioning"
]

def fetch_tags_from_b2b_vault():
    """Dynamically fetch available tags from B2B Vault website"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navigate to B2B Vault
            page.goto("https://www.theb2bvault.com/", timeout=20000)
            page.wait_for_timeout(2000)  # Wait for page to load
            
            # Look for tab elements that contain the category names
            tab_elements = page.locator("a[data-w-tab]").all()
            
            tags = []
            for tab_element in tab_elements:
                try:
                    tab_name = tab_element.get_attribute("data-w-tab")
                    if tab_name and tab_name not in tags:
                        tags.append(tab_name)
                except:
                    continue
            
            browser.close()
            
            # If we successfully found tags, return them
            if tags:
                print(f"✅ Successfully fetched {len(tags)} tags from B2B Vault: {tags}")
                return sorted(tags)  # Sort alphabetically
            else:
                print("⚠️ No tags found, using fallback list")
                return AVAILABLE_TAGS
                
    except Exception as e:
        print(f"⚠️ Error fetching tags from B2B Vault: {e}")
        print("🔄 Using fallback tag list")
        return AVAILABLE_TAGS

# Fetch tags on startup
print("🔍 Fetching available tags from B2B Vault...")
AVAILABLE_TAGS = fetch_tags_from_b2b_vault()

class WebScrapingLogger:
    """Custom logger to capture messages for web interface"""
    def __init__(self):
        self.messages = []
    
    def add_message(self, message):
        self.messages.append({
            'timestamp': time.strftime('%H:%M:%S'),
            'message': message
        })
        # Keep only last 50 messages
        if len(self.messages) > 50:
            self.messages.pop(0)

web_logger = WebScrapingLogger()

def run_scraping_task(selected_tags):
    """Run the scraping task in a separate thread"""
    global scraping_status, web_logger
    
    try:
        scraping_status['is_running'] = True
        scraping_status['progress'] = 0
        scraping_status['current_step'] = 'Initializing...'
        scraping_status['error'] = None
        scraping_status['log_messages'] = []
        web_logger.messages = []
        
        # Filter out "All" if it's selected, as it's not a real tag
        filtered_tags = [tag for tag in selected_tags if tag != "All"]
        
        # If "All" was selected, use all available tags except "All"
        if "All" in selected_tags:
            filtered_tags = [tag for tag in AVAILABLE_TAGS if tag != "All"]
            web_logger.add_message(f"'All' selected - scraping all {len(filtered_tags)} categories")
        
        if not filtered_tags:
            raise Exception("No valid tags selected for scraping")
        
        # Initialize agent with selected tags
        agent = B2BVaultAgent(tabs_to_search=filtered_tags, max_workers=3)
        
        # Step 1: Collect articles
        scraping_status['current_step'] = 'Collecting articles from B2B Vault...'
        scraping_status['progress'] = 10
        web_logger.add_message(f"Starting scraping for tags: {', '.join(filtered_tags)}")
        
        all_articles = []
        for i, tag in enumerate(filtered_tags):
            scraping_status['current_step'] = f'Collecting {tag} articles...'
            scraping_status['progress'] = 10 + (i * 20 // len(filtered_tags))
            web_logger.add_message(f"Collecting articles from {tag} tab...")
            
            try:
                tag_articles = agent.navigate_to_tab_and_get_articles(tag, preview=False)
                all_articles.extend(tag_articles)
                web_logger.add_message(f"Found {len(tag_articles)} articles in {tag} tab")
            except Exception as e:
                web_logger.add_message(f"Error collecting {tag} articles: {str(e)}")
                continue
        
        if not all_articles:
            raise Exception("No articles found for selected tags")
        
        web_logger.add_message(f"Total articles found: {len(all_articles)}")
        
        # Step 2: Process articles
        scraping_status['current_step'] = 'Processing articles with AI...'
        scraping_status['progress'] = 40
        
        try:
            processed_articles = agent.process_multiple_articles_parallel(all_articles, preview=False)
        except Exception as e:
            web_logger.add_message(f"Parallel processing failed: {str(e)}")
            web_logger.add_message("Trying sequential processing...")
            processed_articles = agent.process_multiple_articles(all_articles[:5], preview=False)
        
        if not processed_articles:
            raise Exception("No articles were successfully processed")
        
        web_logger.add_message(f"Successfully processed {len(processed_articles)} articles")
        
        # Step 3: Generate PDF
        scraping_status['current_step'] = 'Generating PDF report...'
        scraping_status['progress'] = 70
        
        try:
            pdf_path = agent.generate_comprehensive_pdf_report(processed_articles, preview=False)
            web_logger.add_message(f"PDF report generated: {os.path.basename(pdf_path)}")
        except Exception as e:
            web_logger.add_message(f"PDF generation failed: {str(e)}")
            pdf_path = None
        
        # Step 4: Generate website
        scraping_status['current_step'] = 'Generating website...'
        scraping_status['progress'] = 85
        
        try:
            website_path = agent.generate_website(processed_articles, pdf_path, preview=False)
            web_logger.add_message(f"Website generated: {website_path}")
        except Exception as e:
            web_logger.add_message(f"Website generation failed: {str(e)}")
            website_path = None
        
        # Complete
        scraping_status['current_step'] = 'Complete!'
        scraping_status['progress'] = 100
        scraping_status['results'] = {
            'total_articles': len(all_articles),
            'processed_articles': len(processed_articles),
            'pdf_path': pdf_path,
            'website_path': website_path,
            'selected_tags': selected_tags,
            'filtered_tags': filtered_tags
        }
        web_logger.add_message("Scraping completed successfully!")
        
    except Exception as e:
        scraping_status['error'] = str(e)
        scraping_status['current_step'] = f'Error: {str(e)}'
        web_logger.add_message(f"ERROR: {str(e)}")
    finally:
        scraping_status['is_running'] = False
        scraping_status['log_messages'] = web_logger.messages

@app.route('/')
def index():
    """Main page with tag selection"""
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>B2B Vault Scraper - Tag Selection</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .header h1 {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2.5rem;
        }
        
        .header p {
            color: #7f8c8d;
            font-size: 1.1rem;
        }
        
        .tag-selection {
            margin-bottom: 30px;
        }
        
        .tag-selection h2 {
            color: #34495e;
            margin-bottom: 20px;
            font-size: 1.3rem;
        }
        
        .tags-info {
            background: #e8f4f8;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 0.9rem;
            color: #2c3e50;
        }
        
        .tags-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
            margin-bottom: 30px;
        }
        
        .tag-checkbox {
            display: none;
        }
        
        .tag-label {
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
        }
        
        .tag-label:hover {
            background: #e9ecef;
            transform: translateY(-2px);
        }
        
        .tag-checkbox:checked + .tag-label {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        .tag-label.all-tag {
            background: #27ae60;
            color: white;
            border-color: #27ae60;
            font-weight: bold;
        }
        
        .tag-checkbox:checked + .tag-label.all-tag {
            background: #219a52;
            border-color: #219a52;
        }
        
        .controls {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .btn {
            padding: 15px 30px;
            margin: 0 10px;
            border: none;
            border-radius: 25px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover:not(:disabled) {
            background: #5a6fd8;
            transform: translateY(-2px);
        }
        
        .btn-secondary {
            background: #95a5a6;
            color: white;
        }
        
        .btn-secondary:hover {
            background: #7f8c8d;
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .progress-container {
            display: none;
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 15px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
            width: 0%;
        }
        
        .progress-text {
            text-align: center;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .log-container {
            background: #2c3e50;
            color: #ecf0f1;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            max-height: 300px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            display: none;
        }
        
        .log-message {
            padding: 2px 0;
        }
        
        .error-message {
            background: #e74c3c;
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            display: none;
        }
        
        .success-message {
            background: #27ae60;
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            display: none;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 20px;
                margin: 10px;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .tags-grid {
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 B2B Vault Scraper</h1>
            <p>Select the categories you want to scrape from B2B Vault and generate AI-powered insights</p>
        </div>
        
        <div class="tag-selection">
            <h2>📑 Select Categories to Scrape:</h2>
            <div class="tags-info">
                💡 <strong>Tip:</strong> Select "All" to scrape every category, or choose specific categories you're interested in. 
                Categories are dynamically fetched from B2B Vault.
            </div>
            <div class="tags-grid" id="tagsGrid">
                {% for tag in available_tags %}
                <div>
                    <input type="checkbox" id="tag-{{ loop.index0 }}" class="tag-checkbox" value="{{ tag }}">
                    <label for="tag-{{ loop.index0 }}" class="tag-label {% if tag == 'All' %}all-tag{% endif %}">
                        {% if tag == 'All' %}🌟 {{ tag }}{% else %}{{ tag }}{% endif %}
                    </label>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div class="controls">
            <button class="btn btn-secondary" onclick="selectAll()">Select All Categories</button>
            <button class="btn btn-secondary" onclick="clearAll()">Clear Selection</button>
            <button class="btn btn-primary" id="startBtn" onclick="startScraping()">Start Scraping</button>
        </div>
        
        <div class="progress-container" id="progressContainer">
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="progress-text" id="progressText">Initializing...</div>
        </div>
        
        <div class="log-container" id="logContainer">
            <div id="logMessages"></div>
        </div>
        
        <div class="error-message" id="errorMessage"></div>
        <div class="success-message" id="successMessage"></div>
    </div>

    <script>
        let pollingInterval;
        
        function selectAll() {
            // Check the "All" checkbox
            const allCheckbox = document.querySelector('input[value="All"]');
            if (allCheckbox) {
                allCheckbox.checked = true;
            }
        }
        
        function clearAll() {
            const checkboxes = document.querySelectorAll('.tag-checkbox');
            checkboxes.forEach(cb => cb.checked = false);
        }
        
        function getSelectedTags() {
            const checkboxes = document.querySelectorAll('.tag-checkbox:checked');
            return Array.from(checkboxes).map(cb => cb.value);
        }
        
        function showError(message) {
            const errorDiv = document.getElementById('errorMessage');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            setTimeout(() => {
                errorDiv.style.display = 'none';
            }, 5000);
        }
        
        function showSuccess(message) {
            const successDiv = document.getElementById('successMessage');
            successDiv.innerHTML = message;
            successDiv.style.display = 'block';
        }
        
        function updateProgress(progress, message) {
            document.getElementById('progressFill').style.width = progress + '%';
            document.getElementById('progressText').textContent = message;
        }
        
        function updateLogs(messages) {
            const logDiv = document.getElementById('logMessages');
            logDiv.innerHTML = messages.map(msg => 
                `<div class="log-message">[${msg.timestamp}] ${msg.message}</div>`
            ).join('');
            logDiv.scrollTop = logDiv.scrollHeight;
        }
        
        function startScraping() {
            const selectedTags = getSelectedTags();
            
            if (selectedTags.length === 0) {
                showError('Please select at least one category to scrape.');
                return;
            }
            
            // Disable button and show progress
            document.getElementById('startBtn').disabled = true;
            document.getElementById('progressContainer').style.display = 'block';
            document.getElementById('logContainer').style.display = 'block';
            
            // Start scraping
            fetch('/start_scraping', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ tags: selectedTags })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showError(data.error);
                    document.getElementById('startBtn').disabled = false;
                    document.getElementById('progressContainer').style.display = 'none';
                } else {
                    // Start polling for status
                    pollingInterval = setInterval(pollStatus, 1000);
                }
            })
            .catch(error => {
                showError('Failed to start scraping: ' + error);
                document.getElementById('startBtn').disabled = false;
                document.getElementById('progressContainer').style.display = 'none';
            });
        }
        
        function pollStatus() {
            fetch('/status')
            .then(response => response.json())
            .then(data => {
                updateProgress(data.progress, data.current_step);
                
                if (data.log_messages) {
                    updateLogs(data.log_messages);
                }
                
                if (data.error) {
                    clearInterval(pollingInterval);
                    showError(data.error);
                    document.getElementById('startBtn').disabled = false;
                } else if (!data.is_running && data.results) {
                    clearInterval(pollingInterval);
                    const tags = data.results.selected_tags.includes('All') ? 
                                 `All categories (${data.results.filtered_tags.length} total)` : 
                                 data.results.selected_tags.join(', ');
                    showSuccess(`
                        🎉 Scraping completed successfully!<br>
                        📊 Processed ${data.results.processed_articles}/${data.results.total_articles} articles<br>
                        📑 Categories: ${tags}<br>
                        <br>
                        <a href="/results" style="color: white; text-decoration: underline;">View Results</a>
                    `);
                    document.getElementById('startBtn').disabled = false;
                }
            })
            .catch(error => {
                console.error('Error polling status:', error);
            });
        }
        
        // Check if scraping is already running on page load
        window.onload = function() {
            fetch('/status')
            .then(response => response.json())
            .then(data => {
                if (data.is_running) {
                    document.getElementById('startBtn').disabled = true;
                    document.getElementById('progressContainer').style.display = 'block';
                    document.getElementById('logContainer').style.display = 'block';
                    pollingInterval = setInterval(pollStatus, 1000);
                }
            });
        };
    </script>
</body>
</html>
    """
    return render_template_string(html_template, available_tags=AVAILABLE_TAGS, scraping_status=scraping_status)

@app.route('/refresh_tags')
def refresh_tags():
    """Endpoint to refresh tags from B2B Vault"""
    global AVAILABLE_TAGS
    try:
        AVAILABLE_TAGS = fetch_tags_from_b2b_vault()
        return jsonify({'success': True, 'tags': AVAILABLE_TAGS, 'count': len(AVAILABLE_TAGS)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    """Start the scraping process with selected tags"""
    if scraping_status['is_running']:
        return jsonify({'error': 'Scraping is already running'}), 400
    
    selected_tags = request.json.get('tags', [])
    if not selected_tags:
        return jsonify({'error': 'No tags selected'}), 400
    
    # Start scraping in background thread
    thread = threading.Thread(target=run_scraping_task, args=(selected_tags,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True})

@app.route('/status')
def get_status():
    """Get current scraping status"""
    return jsonify(scraping_status)

@app.route('/results')
def view_results():
    """View the results page"""
    if not scraping_status['results']:
        return redirect(url_for('index'))
    
    results_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>B2B Vault Scraper - Results</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .header h1 {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2.5rem;
        }
        
        .results-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .result-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border-left: 4px solid #667eea;
        }
        
        .result-number {
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
            display: block;
        }
        
        .result-label {
            color: #7f8c8d;
            font-size: 0.9rem;
            margin-top: 5px;
        }
        
        .tags-section {
            background: #e8f4f8;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        
        .tags-section h3 {
            color: #2c3e50;
            margin-bottom: 15px;
        }
        
        .tag-badge {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            margin: 5px;
            font-size: 0.9rem;
        }
        
        .tag-badge.all-badge {
            background: #27ae60;
        }
        
        .actions {
            text-align: center;
            margin-top: 30px;
        }
        
        .btn {
            display: inline-block;
            padding: 15px 30px;
            margin: 0 10px;
            border: none;
            border-radius: 25px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.3s ease;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5a6fd8;
            transform: translateY(-2px);
        }
        
        .btn-secondary {
            background: #95a5a6;
            color: white;
        }
        
        .btn-secondary:hover {
            background: #7f8c8d;
        }
        
        .btn-success {
            background: #27ae60;
            color: white;
        }
        
        .btn-success:hover {
            background: #219a52;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Scraping Results</h1>
            <p>Your B2B Vault analysis has been completed successfully!</p>
        </div>
        
        <div class="results-grid">
            <div class="result-card">
                <span class="result-number">{{ results.total_articles }}</span>
                <div class="result-label">Total Articles Found</div>
            </div>
            <div class="result-card">
                <span class="result-number">{{ results.processed_articles }}</span>
                <div class="result-label">Articles Processed</div>
            </div>
            <div class="result-card">
                <span class="result-number">{{ results.filtered_tags|length if results.filtered_tags else results.selected_tags|length }}</span>
                <div class="result-label">Categories Scraped</div>
            </div>
        </div>
        
        <div class="tags-section">
            <h3>📑 Scraped Categories:</h3>
            {% if 'All' in results.selected_tags %}
                <span class="tag-badge all-badge">🌟 All Categories</span>
                <p style="margin-top: 10px; color: #666; font-size: 0.9rem;">
                    Scraped {{ results.filtered_tags|length }} categories: {{ results.filtered_tags|join(', ') }}
                </p>
            {% else %}
                {% for tag in results.selected_tags %}
                <span class="tag-badge">{{ tag }}</span>
                {% endfor %}
            {% endif %}
        </div>
        
        <div class="actions">
            <a href="http://localhost:8000" target="_blank" class="btn btn-primary">
                🌐 View Website Dashboard
            </a>
            
            <a href="/generate_netlify_site" class="btn btn-success">
                📤 Generate Netlify Site
            </a>
            
            <a href="/" class="btn btn-secondary">
                🔄 Scrape More Categories
            </a>
        </div>
        
        <script>
            // Auto-start the website server when viewing results
            window.onload = function() {
                setTimeout(() => {
                    const websiteBtn = document.querySelector('.btn-primary');
                    if (websiteBtn) {
                        fetch('/start_website_server')
                        .then(response => response.json())
                        .then(data => {
                            console.log('Website server started');
                        })
                        .catch(error => {
                            console.error('Error starting website server:', error);
                        });
                    }
                }, 1000);
            };
        </script>
    </div>
</body>
</html>
    """
    return render_template_string(results_template, results=scraping_status['results'])

@app.route('/generate_netlify_site')
def generate_netlify_site():
    """Generate an enhanced Netlify-ready static site"""
    try:
        import subprocess
        import sys
        
        # Run the enhanced Netlify deployment script
        result = subprocess.run([sys.executable, 'prepare_netlify_deployment.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({
                'success': True, 
                'message': 'Enhanced Netlify site generated successfully!',
                'output': result.stdout
            })
        else:
            return jsonify({
                'error': f'Failed to generate Netlify site: {result.stderr}'
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/start_website_server')
def start_website_server():
    """Start the website server in background"""
    try:
        import subprocess
        import sys
        
        # Start the website server script in background
        subprocess.Popen([sys.executable, 'start_website.py'], 
                        cwd='/Users/arjansingh/Downloads/B2BVaultScraper')
        
        return jsonify({'success': True, 'message': 'Website server started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate_static_site')
def generate_static_site():
    """Generate a complete static site for Netlify deployment"""
    try:
        # Create netlify_site directory
        netlify_dir = "netlify_site"
        os.makedirs(netlify_dir, exist_ok=True)
        
        # Get the latest scraped data
        scraped_data_dir = "scraped_data"
        
        # Find the latest website
        website_dir = os.path.join(scraped_data_dir, "website")
        if os.path.exists(os.path.join(website_dir, "index.html")):
            # Copy the generated website to netlify_site
            import shutil
            
            # Copy index.html
            src_index = os.path.join(website_dir, "index.html")
            dst_index = os.path.join(netlify_dir, "index.html")
            shutil.copy2(src_index, dst_index)
            
            # Copy any PDF files
            import glob
            pdf_files = glob.glob(os.path.join(scraped_data_dir, "*.pdf"))
            if pdf_files:
                latest_pdf = max(pdf_files, key=os.path.getmtime)
                expected_pdf_name = "b2b_vault_comprehensive_report_20250630_161238.pdf"
                dst_pdf = os.path.join(netlify_dir, expected_pdf_name)
                shutil.copy2(latest_pdf, dst_pdf)
            
            # Create _redirects file for Netlify
            redirects_content = """# Netlify redirects
/pdf /b2b_vault_comprehensive_report_20250630_161238.pdf 302
/* /index.html 200
"""
            with open(os.path.join(netlify_dir, "_redirects"), "w") as f:
                f.write(redirects_content)
            
            # Create netlify.toml
            netlify_toml = """[build]
  publish = "."

[[headers]]
  for = "*.pdf"
  [headers.values]
    Content-Type = "application/pdf"
    
[[headers]]
  for = "*.html"
  [headers.values]
    Content-Type = "text/html; charset=utf-8"
"""
            with open(os.path.join(netlify_dir, "netlify.toml"), "w") as f:
                f.write(netlify_toml)
            
            return jsonify({
                'success': True, 
                'message': f'Static site generated in {netlify_dir}',
                'files': os.listdir(netlify_dir)
            })
        else:
            return jsonify({'error': 'No website data found. Run scraping first.'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting B2B Vault Interactive Scraper...")
    print(f"📑 Found {len(AVAILABLE_TAGS)} categories: {', '.join(AVAILABLE_TAGS)}")
    print("🌐 Open your browser to: http://localhost:5001")
    print("⏹️  Press Ctrl+C to stop the server")
    app.run(host='127.0.0.1', port=5001, debug=False)
