#!/usr/bin/env python3
"""
Web interface for B2B Vault Scraper - scrapes all tags by default
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import threading
import time
from B2Bscraper import B2BVaultAgent
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

# Available tags from B2B Vault - scrape all by default
ALL_TAGS = [
    "Sales",
    "Marketing", 
    "Growth",
    "Product",
    "Leadership",
    "Strategy",
    "Customer Success",
    "Operations",
    "Finance",
    "HR",
    "Technology"
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

def run_scraping_task():
    """Run the scraping task for all tags"""
    global scraping_status, web_logger
    
    try:
        scraping_status['is_running'] = True
        scraping_status['progress'] = 0
        scraping_status['current_step'] = 'Initializing...'
        scraping_status['error'] = None
        scraping_status['log_messages'] = []
        web_logger.messages = []
        
        # Initialize agent with all tags
        agent = B2BVaultAgent(tabs_to_search=ALL_TAGS, max_workers=3)
        
        # Step 1: Collect articles from all tags
        scraping_status['current_step'] = 'Collecting articles from all B2B Vault tags...'
        scraping_status['progress'] = 10
        web_logger.add_message(f"Starting comprehensive scraping for all tags: {', '.join(ALL_TAGS)}")
        
        all_articles = []
        for i, tag in enumerate(ALL_TAGS):
            scraping_status['current_step'] = f'Collecting {tag} articles...'
            scraping_status['progress'] = 10 + (i * 30 // len(ALL_TAGS))
            web_logger.add_message(f"Collecting articles from {tag} tab...")
            
            try:
                tag_articles = agent.navigate_to_tab_and_get_articles(tag, preview=False)
                all_articles.extend(tag_articles)
                web_logger.add_message(f"Found {len(tag_articles)} articles in {tag} tab")
            except Exception as e:
                web_logger.add_message(f"Error collecting {tag} articles: {str(e)}")
                continue
        
        if not all_articles:
            raise Exception("No articles found across all tags")
        
        web_logger.add_message(f"Total articles found across all tags: {len(all_articles)}")
        
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
            'tags_scraped': ALL_TAGS,
            'articles_by_tag': {tag: len([a for a in all_articles if a['tab'] == tag]) for tag in ALL_TAGS}
        }
        web_logger.add_message("Comprehensive scraping completed successfully!")
        web_logger.add_message("You can now filter and search through all articles on the website!")
        
    except Exception as e:
        scraping_status['error'] = str(e)
        scraping_status['current_step'] = f'Error: {str(e)}'
        web_logger.add_message(f"ERROR: {str(e)}")
    finally:
        scraping_status['is_running'] = False
        scraping_status['log_messages'] = web_logger.messages

@app.route('/')
def index():
    """Main page - start comprehensive scraping"""
    return render_template('index.html', 
                         all_tags=ALL_TAGS,
                         scraping_status=scraping_status)

@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    """Start the comprehensive scraping process"""
    if scraping_status['is_running']:
        return jsonify({'error': 'Scraping is already running'}), 400
    
    # Start scraping all tags in background thread
    thread = threading.Thread(target=run_scraping_task)
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

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
