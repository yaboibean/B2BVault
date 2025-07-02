#!/usr/bin/env python3
"""
Simple API server to handle scraping requests from static sites
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time
import os
from B2Bscraper import B2BVaultAgent

app = Flask(__name__)
CORS(app)  # Enable CORS for static site requests

# Global status tracking
scraping_status = {
    'is_running': False,
    'progress': 0,
    'current_step': '',
    'results': None,
    'error': None,
    'log_messages': []
}

def run_scraping_task(selected_tags):
    """Run the scraping task"""
    global scraping_status
    
    try:
        scraping_status['is_running'] = True
        scraping_status['progress'] = 0
        scraping_status['current_step'] = 'Initializing...'
        scraping_status['error'] = None
        
        # Handle "All" selection
        if "All" in selected_tags:
            tags_to_scrape = ["Sales", "Marketing", "AI", "Content Marketing", "Growth"]
        else:
            tags_to_scrape = selected_tags
        
        agent = B2BVaultAgent(tabs_to_search=tags_to_scrape, max_workers=3)
        
        # Collect articles
        scraping_status['current_step'] = 'Collecting articles...'
        scraping_status['progress'] = 20
        
        all_articles = []
        for tag in tags_to_scrape:
            tag_articles = agent.navigate_to_tab_and_get_articles(tag, preview=False)
            all_articles.extend(tag_articles)
        
        # Process articles
        scraping_status['current_step'] = 'Processing with AI...'
        scraping_status['progress'] = 60
        
        processed_articles = agent.process_multiple_articles_parallel(all_articles, preview=False)
        
        # Generate outputs
        scraping_status['current_step'] = 'Generating reports...'
        scraping_status['progress'] = 90
        
        pdf_path = agent.generate_comprehensive_pdf_report(processed_articles, preview=False)
        website_path = agent.generate_website(processed_articles, pdf_path, preview=False)
        
        scraping_status['current_step'] = 'Complete!'
        scraping_status['progress'] = 100
        scraping_status['results'] = {
            'total_articles': len(all_articles),
            'processed_articles': len(processed_articles),
            'selected_tags': tags_to_scrape
        }
        
    except Exception as e:
        scraping_status['error'] = str(e)
        scraping_status['current_step'] = f'Error: {str(e)}'
    finally:
        scraping_status['is_running'] = False

@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    """Start scraping process"""
    if scraping_status['is_running']:
        return jsonify({'error': 'Scraping already running'}), 400
    
    data = request.get_json()
    selected_tags = data.get('tags', [])
    
    if not selected_tags:
        return jsonify({'error': 'No tags selected'}), 400
    
    # Start in background thread
    thread = threading.Thread(target=run_scraping_task, args=(selected_tags,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True})

@app.route('/status')
def get_status():
    """Get scraping status"""
    return jsonify(scraping_status)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)
