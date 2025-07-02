#!/usr/bin/env python3
"""
Web interface for B2B Vault Scraper - scrapes all tags by default
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import threading
import time
from B2Bscraper import B2BVaultAgent
import pickle
import json
from datetime import datetime

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

# Available tags from B2B Vault - use actual tags from the site
ALL_TAGS = [
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

# Cache file path
CACHE_FILE = os.path.join("scraped_data", "articles_cache.pickle")
CACHE_INFO_FILE = os.path.join("scraped_data", "cache_info.json")

def load_cached_articles():
    """Load cached articles from file."""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'rb') as f:
                return pickle.load(f)
        return []
    except Exception as e:
        print(f"Error loading cache: {e}")
        return []

def save_articles_to_cache(articles):
    """Save articles to cache file."""
    try:
        os.makedirs("scraped_data", exist_ok=True)
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(articles, f)
        
        # Save cache info
        cache_info = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'article_count': len(articles),
            'tags': list(set(a.get('tab', 'Unknown') for a in articles))
        }
        with open(CACHE_INFO_FILE, 'w') as f:
            json.dump(cache_info, f)
        
        return True
    except Exception as e:
        print(f"Error saving cache: {e}")
        return False

def get_cache_info():
    """Get information about cached data."""
    try:
        if os.path.exists(CACHE_INFO_FILE):
            with open(CACHE_INFO_FILE, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"Error reading cache info: {e}")
        return None

def run_scraping_task(selected_tags):
    """Run the scraping task for selected tags"""
    global scraping_status, web_logger
    
    try:
        scraping_status['is_running'] = True
        scraping_status['progress'] = 0
        scraping_status['current_step'] = 'Initializing...'
        scraping_status['error'] = None
        scraping_status['log_messages'] = []
        web_logger.messages = []
        
        # Handle "All" selection
        if "All" in selected_tags or len(selected_tags) == len(ALL_TAGS) - 1:  # -1 for "All" option
            tags_to_scrape = [tag for tag in ALL_TAGS if tag != "All"]
            web_logger.add_message("Scraping ALL available tags")
        else:
            tags_to_scrape = selected_tags
        
        # Initialize agent with selected tags
        agent = B2BVaultAgent(tabs_to_search=tags_to_scrape, max_workers=3)
        
        # Step 1: Collect articles from selected tags
        scraping_status['current_step'] = f'Collecting fresh articles from {len(tags_to_scrape)} categories...'
        scraping_status['progress'] = 10
        web_logger.add_message(f"Starting fresh scraping for tags: {', '.join(tags_to_scrape)}")
        
        all_articles = []
        for i, tag in enumerate(tags_to_scrape):
            scraping_status['current_step'] = f'Collecting {tag} articles...'
            scraping_status['progress'] = 10 + (i * 30 // len(tags_to_scrape))
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
        
        # Save to cache
        scraping_status['current_step'] = 'Saving articles to cache...'
        scraping_status['progress'] = 45
        if save_articles_to_cache(all_articles):
            web_logger.add_message(f"Saved {len(all_articles)} articles to cache")
        else:
            web_logger.add_message("Warning: Failed to save articles to cache")
        
        web_logger.add_message(f"Total articles found: {len(all_articles)}")
        
        # Step 2: Process articles
        scraping_status['current_step'] = 'Processing articles with AI...'
        scraping_status['progress'] = 50
        
        try:
            processed_articles = agent.process_multiple_articles_parallel(all_articles, preview=False)
        except Exception as e:
            web_logger.add_message(f"Parallel processing failed: {str(e)}")
            web_logger.add_message("Trying sequential processing...")
            processed_articles = agent.process_multiple_articles(all_articles[:10], preview=False)
        
        if not processed_articles:
            raise Exception("No articles were successfully processed")
        
        web_logger.add_message(f"Successfully processed {len(processed_articles)} articles")
        
        # Step 3: Generate PDF
        scraping_status['current_step'] = 'Generating comprehensive PDF report...'
        scraping_status['progress'] = 80
        
        try:
            pdf_path = agent.generate_comprehensive_pdf_report(processed_articles, preview=False)
            web_logger.add_message(f"PDF report generated: {os.path.basename(pdf_path)}")
        except Exception as e:
            web_logger.add_message(f"PDF generation failed: {str(e)}")
            pdf_path = None
        
        # Step 4: Generate searchable website
        scraping_status['current_step'] = 'Generating searchable website...'
        scraping_status['progress'] = 90
        
        try:
            website_path = agent.generate_website(processed_articles, pdf_path, preview=False)
            web_logger.add_message(f"Interactive website generated: {website_path}")
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
            'tags_scraped': tags_to_scrape,
            'articles_by_tag': {tag: len([a for a in all_articles if a['tab'] == tag]) for tag in tags_to_scrape}
        }
        web_logger.add_message("Scraping completed successfully!")
        web_logger.add_message("You can now filter and search through all articles on the website!")
        
    except Exception as e:
        scraping_status['error'] = str(e)
        scraping_status['current_step'] = f'Error: {str(e)}'
        web_logger.add_message(f"ERROR: {str(e)}")
    finally:
        scraping_status['is_running'] = False
        scraping_status['log_messages'] = web_logger.messages

def run_cached_processing_task(selected_tags):
    """Process cached articles for selected tags."""
    global scraping_status, web_logger
    
    try:
        scraping_status['is_running'] = True
        scraping_status['progress'] = 0
        scraping_status['current_step'] = 'Loading cached data...'
        scraping_status['error'] = None
        scraping_status['log_messages'] = []
        web_logger.messages = []
        
        # Load cached articles
        cached_articles = load_cached_articles()
        if not cached_articles:
            raise Exception("No cached articles found. Please scrape fresh data first.")
        
        web_logger.add_message(f"Loaded {len(cached_articles)} articles from cache")
        
        # Filter by selected tags
        if "All" not in selected_tags:
            filtered_articles = [a for a in cached_articles if a.get('tab') in selected_tags]
        else:
            filtered_articles = cached_articles
        
        if not filtered_articles:
            raise Exception(f"No cached articles found for selected tags: {', '.join(selected_tags)}")
        
        web_logger.add_message(f"Using {len(filtered_articles)} articles for selected tags")
        scraping_status['progress'] = 20
        
        # Initialize agent for processing only
        agent = B2BVaultAgent(tabs_to_search=selected_tags, max_workers=3)
        
        # Process the cached articles
        process_articles_and_generate_outputs(agent, filtered_articles, selected_tags)
        
    except Exception as e:
        scraping_status['error'] = str(e)
        scraping_status['current_step'] = f'Error: {str(e)}'
        web_logger.add_message(f"ERROR: {str(e)}")
    finally:
        scraping_status['is_running'] = False
        scraping_status['log_messages'] = web_logger.messages

def process_articles_and_generate_outputs(agent, all_articles, tags_used):
    """Common function to process articles and generate outputs."""
    global scraping_status, web_logger
    
    # Step 2: Process articles with AI
    scraping_status['current_step'] = 'Processing articles with AI...'
    scraping_status['progress'] = 50
    
    try:
        processed_articles = agent.process_multiple_articles_parallel(all_articles, preview=False)
    except Exception as e:
        web_logger.add_message(f"Parallel processing failed: {str(e)}")
        web_logger.add_message("Trying sequential processing...")
        processed_articles = agent.process_multiple_articles(all_articles[:10], preview=False)
    
    if not processed_articles:
        raise Exception("No articles were successfully processed")
    
    web_logger.add_message(f"Successfully processed {len(processed_articles)} articles")
    
    # Step 3: Generate PDF
    scraping_status['current_step'] = 'Generating comprehensive PDF report...'
    scraping_status['progress'] = 80
    
    try:
        pdf_path = agent.generate_comprehensive_pdf_report(processed_articles, preview=False)
        web_logger.add_message(f"PDF report generated: {os.path.basename(pdf_path)}")
    except Exception as e:
        web_logger.add_message(f"PDF generation failed: {str(e)}")
        pdf_path = None
    
    # Step 4: Generate website
    scraping_status['current_step'] = 'Generating searchable website...'
    scraping_status['progress'] = 90
    
    try:
        website_path = agent.generate_website(processed_articles, pdf_path, preview=False)
        web_logger.add_message(f"Interactive website generated: {website_path}")
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
        'tags_scraped': tags_used,
        'articles_by_tag': {tag: len([a for a in all_articles if a['tab'] == tag]) for tag in tags_used}
    }
    web_logger.add_message("Processing completed successfully!")
    web_logger.add_message("You can now filter and search through all articles on the website!")

def run_comprehensive_scraping():
    """Run comprehensive scraping of ALL B2B Vault articles from homepage"""
    global scraping_status, web_logger
    
    try:
        scraping_status['is_running'] = True
        scraping_status['progress'] = 0
        scraping_status['current_step'] = 'Initializing comprehensive scraping...'
        scraping_status['error'] = None
        scraping_status['log_messages'] = []
        web_logger.messages = []
        
        web_logger.add_message("🚀 Starting comprehensive B2B Vault scraping")
        web_logger.add_message("📊 Will collect ALL articles from homepage")
        
        # Initialize agent for comprehensive scraping
        agent = B2BVaultAgent(max_workers=5)
        
        # Step 1: Collect ALL articles from homepage
        scraping_status['current_step'] = 'Discovering and collecting ALL articles from homepage...'
        scraping_status['progress'] = 10
        web_logger.add_message("📂 Scanning homepage for all articles...")
        
        all_articles = agent.scrape_all_articles_from_homepage(preview=False)
        
        if not all_articles:
            raise Exception("No articles found on homepage")
        
        web_logger.add_message(f"✅ Collected {len(all_articles)} total articles from homepage")
        web_logger.add_message(f"📂 Found articles from {len(set(a['tab'] for a in all_articles))} categories")
        web_logger.add_message(f"📰 From {len(set(a['publisher'] for a in all_articles))} publishers")
        
        # Step 2: Process ALL articles
        scraping_status['current_step'] = 'Processing ALL articles with AI...'
        scraping_status['progress'] = 40
        
        processed_articles = agent.process_multiple_articles_parallel(all_articles, preview=False)
        
        if not processed_articles:
            raise Exception("No articles were successfully processed")
        
        web_logger.add_message(f"🤖 Successfully processed {len(processed_articles)} articles")
        
        # Step 3: Generate comprehensive outputs
        scraping_status['current_step'] = 'Generating comprehensive PDF report...'
        scraping_status['progress'] = 80
        
        pdf_path = agent.generate_comprehensive_pdf_report(processed_articles, preview=False)
        web_logger.add_message(f"📄 Generated comprehensive PDF report")
        
        # Step 4: Generate advanced website
        scraping_status['current_step'] = 'Building advanced website with filtering...'
        scraping_status['progress'] = 90
        
        website_path = agent.generate_website(processed_articles, pdf_path, preview=False)
        web_logger.add_message(f"🌐 Generated website with all homepage articles")
        
        # Complete
        scraping_status['current_step'] = 'Complete!'
        scraping_status['progress'] = 100
        scraping_status['results'] = {
            'total_articles': len(all_articles),
            'processed_articles': len(processed_articles),
            'pdf_path': pdf_path,
            'website_path': website_path,
            'categories_count': len(set(a['tab'] for a in all_articles)),
            'publishers_count': len(set(a['publisher'] for a in all_articles)),
            'articles_by_category': {cat: len([a for a in all_articles if a['tab'] == cat]) 
                                   for cat in set(a['tab'] for a in all_articles)}
        }
        web_logger.add_message("🎉 Comprehensive homepage scraping completed successfully!")
        web_logger.add_message(f"📊 Final stats: {len(processed_articles)} articles processed from homepage")
        
    except Exception as e:
        scraping_status['error'] = str(e)
        scraping_status['current_step'] = f'Error: {str(e)}'
        web_logger.add_message(f"❌ ERROR: {str(e)}")
    finally:
        scraping_status['is_running'] = False
        scraping_status['log_messages'] = web_logger.messages

@app.route('/')
def index():
    """Main page with tag selection and cache info."""
    cache_info = get_cache_info()
    cached_data_available = cache_info is not None
    
    return render_template('index.html', 
                         available_tags=ALL_TAGS,
                         scraping_status=scraping_status,
                         cached_data_available=cached_data_available,
                         cache_date=cache_info.get('date', '') if cache_info else '',
                         cached_articles_count=cache_info.get('article_count', 0) if cache_info else 0)

@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    """Start the scraping process with selected tags"""
    if scraping_status['is_running']:
        return jsonify({'error': 'Scraping is already running'}), 400
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        selected_tags = data.get('tags', [])
        if not selected_tags:
            return jsonify({'error': 'No tags selected'}), 400
        
        # Start scraping in background thread
        thread = threading.Thread(target=run_scraping_task, args=(selected_tags,))
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': f'Invalid request: {str(e)}'}), 400

@app.route('/status')
def get_status():
    """Get current scraping status"""
    return jsonify(scraping_status)

@app.route('/results')
def view_results():
    """View the results page"""
    if not scraping_status['results']:
        return redirect(url_for('index'))
    return render_template('results.html', results=scraping_status['results'])

@app.route('/view_website')
def view_website():
    """Redirect to the generated website"""
    if scraping_status['results'] and scraping_status['results']['website_path']:
        website_dir = os.path.dirname(scraping_status['results']['website_path'])
        # Start a simple server for the website
        import subprocess
        import webbrowser
        
        # Open the website in browser
        webbrowser.open('http://localhost:8001')
        return jsonify({'success': True, 'message': 'Website opened in browser'})
    return jsonify({'error': 'No website available'}), 404

@app.route('/get_cached_tags')
def get_cached_tags():
    """Get available tags from cached data."""
    cache_info = get_cache_info()
    if cache_info:
        return jsonify({'tags': cache_info.get('tags', [])})
    return jsonify({'error': 'No cached data available'}), 404

@app.route('/process_cached', methods=['POST'])
def process_cached():
    """Process cached data for selected tags."""
    if scraping_status['is_running']:
        return jsonify({'error': 'Processing is already running'}), 400
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        selected_tags = data.get('tags', [])
        if not selected_tags:
            return jsonify({'error': 'No tags selected'}), 400
        
        # Start processing cached data in background thread
        thread = threading.Thread(target=run_cached_processing_task, args=(selected_tags,))
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': f'Invalid request: {str(e)}'}), 400

@app.route('/start_smart_scraping', methods=['POST'])
def start_smart_scraping():
    """Start the smart scraping process"""
    if scraping_status['is_running']:
        return jsonify({'error': 'Scraping is already running'}), 400
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        article_limit = data.get('article_limit', 100)
        processing_mode = data.get('processing_mode', 'auto')
        
        if article_limit < 10 or article_limit > 500:
            return jsonify({'error': 'Article limit must be between 10 and 500'}), 400
        
        # Start smart scraping in background thread
        thread = threading.Thread(target=run_smart_scraping_task, args=(article_limit, processing_mode))
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': f'Invalid request: {str(e)}'}), 400

def run_smart_scraping_task(article_limit, processing_mode):
    """Run the smart scraping task with random article selection"""
    global scraping_status, web_logger
    
    try:
        scraping_status['is_running'] = True
        scraping_status['progress'] = 0
        scraping_status['current_step'] = 'Initializing memory-optimized scraping...'
        scraping_status['error'] = None
        scraping_status['log_messages'] = []
        web_logger.messages = []
        
        # Cap article limit for memory efficiency
        if article_limit > 100:
            article_limit = 100
            web_logger.add_message(f"⚠️ Article limit capped at 100 for memory efficiency")
        
        web_logger.add_message(f"🎲 Starting memory-optimized scraping with {article_limit} articles")
        web_logger.add_message(f"⚙️ Processing mode: {processing_mode}")
        web_logger.add_message(f"💾 Optimized for lower memory usage")
        
        # Initialize agent for memory-optimized scraping
        agent = B2BVaultAgent(max_workers=2)  # Always use 2 workers for memory efficiency
        
        # Step 1: Discover and randomly select articles
        scraping_status['current_step'] = f'Discovering articles and randomly selecting {article_limit}...'
        scraping_status['progress'] = 10
        web_logger.add_message("📂 Scanning B2B Vault homepage for articles...")
        
        all_articles = agent.scrape_all_articles_from_homepage(preview=False, max_articles=article_limit)
        
        if not all_articles:
            raise Exception("No articles found on homepage")
        
        web_logger.add_message(f"✅ Selected {len(all_articles)} random articles for processing")
        web_logger.add_message(f"📂 Categories: {len(set(a['tab'] for a in all_articles))}")
        web_logger.add_message(f"📰 Publishers: {len(set(a['publisher'] for a in all_articles))}")
        
        # Step 2: Process articles based on mode (prefer sequential for memory)
        scraping_status['current_step'] = 'Processing articles with AI...'
        scraping_status['progress'] = 50
        
        if processing_mode == "parallel":
            web_logger.add_message("⚡ Using parallel processing (higher memory usage)")
            try:
                processed_articles = agent.process_multiple_articles_parallel(all_articles, preview=False)
            except Exception as e:
                web_logger.add_message(f"⚠️ Parallel failed, switching to sequential: {str(e)}")
                processed_articles = agent.process_multiple_articles(all_articles[:25], preview=False)
        else:  # sequential or auto - prefer sequential for memory
            web_logger.add_message("🔄 Using sequential processing (memory-efficient)")
            processed_articles = agent.process_multiple_articles(all_articles, preview=False)
        
        if not processed_articles:
            raise Exception("No articles were successfully processed")
        
        web_logger.add_message(f"🤖 Successfully processed {len(processed_articles)} articles")
        
        # Step 3: Generate outputs
        scraping_status['current_step'] = 'Generating reports and website...'
        scraping_status['progress'] = 80
        
        try:
            pdf_path = agent.generate_comprehensive_pdf_report(processed_articles, preview=False)
            web_logger.add_message(f"📄 Generated PDF report")
        except Exception as e:
            web_logger.add_message(f"⚠️ PDF generation failed: {str(e)}")
            pdf_path = None
        
        try:
            website_path = agent.generate_website(processed_articles, pdf_path, preview=False)
            web_logger.add_message(f"🌐 Generated interactive website")
        except Exception as e:
            web_logger.add_message(f"⚠️ Website generation failed: {str(e)}")
            website_path = None
        
        # Complete
        scraping_status['current_step'] = 'Complete!'
        scraping_status['progress'] = 100
        scraping_status['results'] = {
            'total_articles': len(all_articles),
            'processed_articles': len(processed_articles),
            'pdf_path': pdf_path,
            'website_path': website_path,
            'categories_count': len(set(a['tab'] for a in all_articles)),
            'publishers_count': len(set(a['publisher'] for a in all_articles)),
            'processing_mode': processing_mode,
            'article_limit': article_limit
        }
        web_logger.add_message("🎉 Memory-optimized scraping completed successfully!")
        
    except Exception as e:
        scraping_status['error'] = str(e)
        scraping_status['current_step'] = f'Error: {str(e)}'
        web_logger.add_message(f"❌ ERROR: {str(e)}")
    finally:
        scraping_status['is_running'] = False
        scraping_status['log_messages'] = web_logger.messages

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
