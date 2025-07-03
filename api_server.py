#!/usr/bin/env python3
"""
Updated API server for smart random scraping (no tag selection needed)
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time
import os
from B2Bscraper import B2BVaultAgent

app = Flask(__name__)
CORS(app)

# Global status tracking
scraping_status = {
    'is_running': False,
    'progress': 0,
    'current_step': '',
    'results': None,
    'error': None,
    'log_messages': []
}

def run_smart_scraping_task(article_limit=100):
    """Run the smart scraping task with random article selection"""
    global scraping_status
    
    try:
        scraping_status['is_running'] = True
        scraping_status['progress'] = 0
        scraping_status['current_step'] = 'Initializing smart scraping...'
        scraping_status['error'] = None
        
        # Initialize agent for smart scraping
        agent = B2BVaultAgent(max_workers=2)
        
        scraping_status['current_step'] = f'Discovering and randomly selecting {article_limit} articles...'
        scraping_status['progress'] = 20
        
        # Step 1: Get random articles from homepage
        all_articles = agent.scrape_all_articles_from_homepage(preview=False, max_articles=article_limit)
        
        if not all_articles:
            raise Exception("No articles found on homepage")
        
        scraping_status['current_step'] = 'Processing articles with AI...'
        scraping_status['progress'] = 60
        
        # Step 2: Process with AI
        try:
            processed_articles = agent.process_multiple_articles_parallel(all_articles, preview=False)
        except Exception as e:
            # Fallback to sequential processing
            processed_articles = agent.process_multiple_articles(all_articles[:20], preview=False)
        
        if not processed_articles:
            raise Exception("No articles were successfully processed")
        
        scraping_status['current_step'] = 'Generating reports...'
        scraping_status['progress'] = 90
        
        # Step 3: Generate outputs
        pdf_path = agent.generate_comprehensive_pdf_report(processed_articles, preview=False)
        website_path = agent.generate_website(processed_articles, pdf_path, preview=False)
        
        scraping_status['current_step'] = 'Complete!'
        scraping_status['progress'] = 100
        scraping_status['results'] = {
            'total_articles': len(all_articles),
            'processed_articles': len(processed_articles),
            'categories_count': len(set(a['tab'] for a in all_articles)),
            'publishers_count': len(set(a['publisher'] for a in all_articles)),
            'article_limit': article_limit
        }
        
    except Exception as e:
        scraping_status['error'] = str(e)
        scraping_status['current_step'] = f'Error: {str(e)}'
    finally:
        scraping_status['is_running'] = False

@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    """Start smart scraping process (no tags needed)"""
    if scraping_status['is_running']:
        return jsonify({'error': 'Scraping already running'}), 400
    
    data = request.get_json()
    article_limit = data.get('article_limit', 100) if data else 100
    
    thread = threading.Thread(target=run_smart_scraping_task, args=(article_limit,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True})

@app.route('/status')
def get_status():
    """Get scraping status"""
    return jsonify(scraping_status)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)
