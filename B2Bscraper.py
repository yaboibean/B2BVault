import os
import time
import requests
import logging
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from weasyprint import HTML
import concurrent.futures
import asyncio
from typing import List, Dict

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Config
PERPLEXITY_API_KEY = "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"
BASE_URL = "https://www.theb2bvault.com/"

def safe_get_title(card):
    """Extract title from card element."""
    try:
        all_text = card.inner_text()
        
        if "Published by:" in all_text:
            parts = all_text.split("Published by:", 1)
            if len(parts) == 2:
                after_published = parts[1].strip()
                
                publishers = [
                    "ProductLed", "Growth Unhinged", "Gong", "Klue", "April Dunford", 
                    "Navattic", "Chili Piper", "Trigify", "HeyReach", "MRR Unlocked",
                    "HockeyStack", "Crossbeam", "UserGems", "The CMO", "Marketing Week",
                    "Demand Curve"
                ]
                
                for publisher in publishers:
                    if after_published.startswith(publisher):
                        title_text = after_published[len(publisher):].strip()
                        
                        if "Read Full Article" in title_text:
                            title_text = title_text.split("Read Full Article")[0].strip()
                        if "Read Summary" in title_text:
                            title_text = title_text.split("Read Summary")[0].strip()
                        
                        sentences = title_text.split('.')
                        if sentences and len(sentences[0].strip()) > 10:
                            potential_title = sentences[0].strip()
                            if len(potential_title) < 200:
                                return potential_title
        
        # Fallback: find reasonable title in text
        lines = all_text.split('\n')
        for line in lines:
            line = line.strip()
            if (len(line) > 20 and len(line) < 150 and 
                not line.lower().startswith(('copy', 'positioning', 'sales', 'published by', 'read full', 'read summary'))):
                return line
        
        return "Untitled Article"
    except:
        return "Untitled Article"

def safe_get_publisher(card):
    """Extract publisher from card element."""
    try:
        all_text = card.inner_text()
        
        if "Published by:" in all_text:
            after_published = all_text.split("Published by:", 1)[1].strip()
            
            publishers = [
                "ProductLed", "Growth Unhinged", "Gong", "Klue", "April Dunford", 
                "Navattic", "Chili Piper", "Trigify", "HeyReach", "MRR Unlocked",
                "HockeyStack", "Crossbeam", "UserGems", "The CMO", "Marketing Week",
                "Demand Curve"
            ]
            
            for publisher in publishers:
                if after_published.startswith(publisher):
                    return publisher
            
            # Fallback
            words = after_published.split()
            if len(words) >= 1:
                return words[0]
        
        return "Unknown Publisher"
    except:
        return "Unknown Publisher"

class B2BVaultAgent:
    """B2B Vault scraper and analyzer."""
    
    def __init__(self, output_dir: str = "scraped_data", max_workers: int = 5):
        self.output_dir = output_dir
        # Get ALL available tabs automatically
        self.tabs_to_search = self.get_all_available_tabs()
        self.max_workers = max_workers
        os.makedirs(output_dir, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def get_all_available_tabs(self):
        """Automatically discover all available tabs on B2B Vault."""
        all_tabs = [
            "Content Marketing", "Demand Generation", "ABM & GTM", "Paid Marketing",
            "Marketing Ops", "Event Marketing", "AI", "Product Marketing", "Sales",
            "General", "Affiliate & Partnerships", "Copy & Positioning", "Leadership",
            "Strategy", "Customer Success", "Operations", "Finance", "HR", "Technology"
        ]
        return all_tabs

    def scrape_all_articles(self, preview: bool = False):
        """Scrape ALL articles from ALL tabs on B2B Vault."""
        if preview:
            print("🌐 Starting comprehensive B2B Vault scraping...")
            print(f"📂 Will scrape from {len(self.tabs_to_search)} categories")
        
        all_articles = []
        successful_tabs = []
        
        for i, tab_name in enumerate(self.tabs_to_search):
            if preview:
                print(f"\n📑 [{i+1}/{len(self.tabs_to_search)}] Scraping {tab_name}...")
            
            try:
                tab_articles = self.navigate_to_tab_and_get_articles(tab_name, preview)
                if tab_articles:
                    all_articles.extend(tab_articles)
                    successful_tabs.append(tab_name)
                    if preview:
                        print(f"   ✅ Found {len(tab_articles)} articles in {tab_name}")
                else:
                    if preview:
                        print(f"   ⚠️ No articles found in {tab_name}")
            except Exception as e:
                if preview:
                    print(f"   ❌ Error scraping {tab_name}: {e}")
                continue
        
        if preview:
            print(f"\n🎯 Scraping Summary:")
            print(f"   📊 Total articles collected: {len(all_articles)}")
            print(f"   ✅ Successful tabs: {len(successful_tabs)}")
            print(f"   📂 Categories: {', '.join(successful_tabs)}")
        
        return all_articles

    def navigate_to_tab_and_get_articles(self, tab_name: str, preview: bool = False):
        """Navigate to tab and collect ALL article URLs (no limits)."""
        articles = []
        seen_urls = set()
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=not preview)
            page = browser.new_page()
            
            try:
                page.goto(BASE_URL, timeout=30000)
                page.wait_for_timeout(1000)
                
                # Navigate to tab
                page.wait_for_selector(f"a[data-w-tab='{tab_name}']", timeout=10000)
                tab = page.locator(f"a[data-w-tab='{tab_name}']")
                tab.click()
                page.wait_for_timeout(2000)
                
                # Aggressive scrolling to load ALL content
                previous_count = 0
                scroll_attempts = 0
                max_scroll_attempts = 20
                
                while scroll_attempts < max_scroll_attempts:
                    # Scroll to bottom
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(3000)
                    
                    # Check if more content loaded
                    current_count = page.locator("div.w-dyn-item").count()
                    if current_count == previous_count:
                        scroll_attempts += 1
                    else:
                        scroll_attempts = 0  # Reset if new content loaded
                        previous_count = current_count
                    
                    if preview and scroll_attempts == 0:
                        print(f"      📄 Loaded {current_count} items so far...")
                
                # Process ALL cards
                cards = page.locator("div.w-dyn-item")
                total_count = cards.count()
                
                if preview:
                    print(f"      🔍 Processing {total_count} total cards...")
                
                for i in range(total_count):
                    try:
                        card = cards.nth(i)
                        
                        # Check if article matches current tab
                        is_target_article = False
                        try:
                            tag_elements = card.locator("div.text-block-3").all()
                            for tag_element in tag_elements:
                                tag_text = tag_element.inner_text().strip().lower()
                                if tab_name.lower() in tag_text:
                                    is_target_article = True
                                    break
                        except:
                            continue
                        
                        if not is_target_article:
                            continue
                        
                        # Get URL
                        href = None
                        try:
                            buttons = card.locator("a.button-primary-small").all()
                            if buttons:
                                href = buttons[0].get_attribute("href")
                        except:
                            continue
                        
                        if href and href.startswith("http") and href not in seen_urls:
                            seen_urls.add(href)
                            
                            title = safe_get_title(card)
                            publisher = safe_get_publisher(card)

                            articles.append({
                                "title": title,
                                "publisher": publisher,
                                "url": href,
                                "tab": tab_name,
                                "scraped_at": time.strftime('%Y-%m-%d %H:%M:%S')
                            })
                    except Exception as e:
                        continue
                
                if preview:
                    print(f"      ✅ Collected {len(articles)} unique {tab_name} articles")
                
            except Exception as e:
                self.logger.error(f"Error navigating to {tab_name} tab: {e}")
                raise
            finally:
                browser.close()
        
        return articles

    async def scrape_article_content_async(self, article_url: str, browser_context) -> str:
        """Async article content scraping."""
        try:
            page = await browser_context.new_page()
            await page.goto(article_url, timeout=20000)
            await page.wait_for_load_state("domcontentloaded")
            
            content = await page.content()
            await page.close()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract title
            title = "Untitled"
            for selector in ["h1", ".article-title", ".post-title", "title"]:
                title_elem = soup.select_one(selector)
                if title_elem and title_elem.get_text(strip=True):
                    title = title_elem.get_text(strip=True)
                    break
            
            # Extract body
            body_text = ""
            for selector in ["article", ".article-content", ".post-content", ".content", "main", ".rich-text"]:
                body_elem = soup.select_one(selector)
                if body_elem:
                    body_text = body_elem.get_text("\n", strip=True)
                    break
            
            if not body_text:
                paragraphs = soup.find_all("p")
                body_text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            
            return f"Title: {title}\n\nContent:\n{body_text}"
            
        except Exception as e:
            self.logger.error(f"Error scraping article {article_url}: {e}")
            return ""

    async def process_articles_batch_async(self, articles_batch: List[Dict], preview: bool = False) -> List[Dict]:
        """Process articles batch with parallel scraping and API calls."""
        processed_articles = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            
            # Scrape all articles in parallel
            scrape_tasks = []
            for article in articles_batch:
                task = self.scrape_article_content_async(article['url'], context)
                scrape_tasks.append((article, task))
            
            # Wait for scraping
            scraped_results = []
            for article, task in scrape_tasks:
                try:
                    content = await task
                    if content:
                        scraped_results.append((article, content))
                except Exception as e:
                    self.logger.error(f"Error scraping article '{article['title']}': {e}")
                    continue
            
            await browser.close()
        
        # Process with Perplexity API in parallel
        if scraped_results:
            def process_single_article(article_content_pair):
                article, content = article_content_pair
                try:
                    summary = self.send_to_perplexity(content)
                    return {
                        **article,
                        'content': content,
                        'summary': summary
                    }
                except Exception as e:
                    self.logger.error(f"Error processing article '{article['title']}': {e}")
                    return None
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(self.max_workers, 5)) as executor:
                results = list(executor.map(process_single_article, scraped_results))
                processed_articles = [r for r in results if r is not None]
        
        return processed_articles

    def process_multiple_articles_parallel(self, articles: List[Dict], preview: bool = False) -> List[Dict]:
        """Process articles using parallel execution."""
        if preview:
            print(f"\n🔄 Processing {len(articles)} articles in parallel...")
        
        batch_size = min(self.max_workers, 8)
        article_batches = [articles[i:i + batch_size] for i in range(0, len(articles), batch_size)]
        
        all_processed_articles = []
        
        for batch_idx, batch in enumerate(article_batches):
            if preview:
                print(f"\n📦 Processing batch {batch_idx + 1}/{len(article_batches)} ({len(batch)} articles)...")
            
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                processed_batch = loop.run_until_complete(
                    self.process_articles_batch_async(batch, preview)
                )
                all_processed_articles.extend(processed_batch)
                
                if preview:
                    print(f"   ✅ Batch {batch_idx + 1} completed: {len(processed_batch)}/{len(batch)} articles processed")
                
            except Exception as e:
                self.logger.error(f"Error processing batch {batch_idx + 1}: {e}")
            finally:
                loop.close()
        
        return all_processed_articles

    def send_to_perplexity(self, article_content: str) -> str:
        """Send article content to Perplexity API."""
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""
        Analyze this B2B sales article and provide:
        1. A short 1-sentence TL;DR at the very top (around 40 words)
        2. 3-5 key takeaways
        3. Notable companies/technologies
        4. 3-5 actionable recommendations for B2B sales

        NO BOLD OR ITALICS. NO MARKDOWN. NO FORMATTING. JUST TEXT AND SPACING.
        NO CITATIONS. NO SOURCES. NO REFERENCES.

        Article: {article_content[:4000]}
        """
        
        payload = {
            "model": "sonar",
            "messages": [
                {"role": "system", "content": "You are a B2B sales analyst. Always write complete sentences that end with proper punctuation."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 600,
            "temperature": 0.5
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            result = response.json()
            summary = result["choices"][0]["message"]["content"]
            
            # Clean up TL;DR if needed
            lines = summary.splitlines()
            if lines and "TL;DR" in lines[0]:
                tldr_line = lines[0].rstrip('.').rstrip()
                if tldr_line.endswith('..'):
                    tldr_line = tldr_line.rstrip('.')
                if not tldr_line.endswith('.'):
                    tldr_line += '.'
                lines[0] = tldr_line
                summary = "\n".join(lines)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Perplexity API error: {e}")
            return "Analysis failed"

    def generate_comprehensive_pdf_report(self, processed_articles: List[Dict], preview: bool = False):
        """Generate comprehensive PDF report."""
        self.logger.info("Generating comprehensive PDF report")
        if preview:
            print(f"📄 Generating comprehensive PDF report with {len(processed_articles)} articles...")
        
        articles_html = ""
        for i, article in enumerate(processed_articles):
            summary_html = article['summary'].replace('\n', '<br>')
            publisher = article.get('publisher', 'Unknown Publisher')
            
            articles_html += f"""
            <div class="article-section">
                <h2>Article {i+1}: {article['title']}</h2>
                <div class="article-meta">
                    <p><strong>Publisher:</strong> {publisher}</p>
                    <p><strong>URL:</strong> <a href="{article['url']}">{article['url']}</a></p>
                    <p><strong>Tab:</strong> {article['tab']}</p>
                    <p><strong>Processed:</strong> {article['scraped_at']}</p>
                </div>
                <div class="article-summary">
                    <h3>AI Analysis Summary</h3>
                    {summary_html}
                </div>
            </div>
            {'<div class="page-break"></div>' if i < len(processed_articles) - 1 else ''}
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
                h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 15px; text-align: center; }}
                h2 {{ color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; margin-top: 30px; }}
                h3 {{ color: #2980b9; margin-top: 25px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 30px; text-align: center; }}
                .article-section {{ margin-bottom: 40px; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; background-color: #fafafa; }}
                .article-meta {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .article-meta p {{ margin: 5px 0; }}
                .article-summary {{ background-color: white; padding: 20px; border-radius: 5px; border-left: 4px solid #3498db; }}
                .page-break {{ page-break-before: always; }}
                a {{ color: #3498db; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>B2B Vault Comprehensive Analysis Report</h1>
                <p><strong>Total Articles Analyzed:</strong> {len(processed_articles)}</p>
                <p><strong>Generated:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Tabs Searched:</strong> {', '.join(self.tabs_to_search)}</p>
            </div>
            {articles_html}
        </body>
        </html>
        """
        
        try:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"b2b_vault_comprehensive_report_{timestamp}.pdf"
            output_path = os.path.join(self.output_dir, filename)
            HTML(string=html_content).write_pdf(output_path)
            self.logger.info(f"Comprehensive PDF report generated: {output_path}")
            if preview:
                print(f"   ✅ PDF saved to: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive PDF: {e}")
            raise

    def generate_website(self, processed_articles: List[Dict], pdf_path: str = None, preview: bool = False):
        """Generate a static website to display all analyzed articles with search functionality."""
        self.logger.info("Generating static website")
        if preview:
            print("🌐 Generating static website...")
        
        # Create website directory
        website_dir = os.path.join(self.output_dir, "website")
        os.makedirs(website_dir, exist_ok=True)
        
        # Generate article cards HTML
        articles_html = ""
        for i, article in enumerate(processed_articles):
            summary_preview = article['summary'][:200] + "..." if len(article['summary']) > 200 else article['summary']
            word_count = len(article['summary'].split())
            publisher = article.get('publisher', 'Unknown Publisher')
            
            articles_html += f"""
            <div class="article-card" id="article-{i}">
                <div class="article-header">
                    <h2 class="article-title">{article['title']}</h2>
                    <div class="article-meta">
                        <span class="tab-badge">{article['tab']}</span>
                        <span class="publisher">📰 {publisher}</span>
                        <span class="date">{article['scraped_at']}</span>
                        <span class="word-count">{word_count} words</span>
                    </div>
                </div>
                <div class="article-preview">
                    <p>{summary_preview}</p>
                    <button class="expand-btn" onclick="toggleArticle({i})">Read Full Summary</button>
                </div>
                <div class="article-full" id="full-{i}" style="display: none;">
                    <div class="summary-content">
                        {article['summary'].replace(chr(10), '<br>')}
                    </div>
                    <div class="article-link">
                        <a href="{article['url']}" target="_blank" class="source-link">View Original Article</a>
                    </div>
                </div>
            </div>
            """
        
        # PDF download link
        pdf_link = ""
        if pdf_path and os.path.exists(pdf_path):
            pdf_filename = os.path.basename(pdf_path)
            # Copy PDF to website directory
            import shutil
            pdf_dest = os.path.join(website_dir, pdf_filename)
            shutil.copy2(pdf_path, pdf_dest)
            pdf_link = f'<a href="{pdf_filename}" class="btn btn-download" download>📄 Download PDF Report</a>'
        
        # Generate main HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>B2B Vault Analysis - {len(processed_articles)} Articles</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f4f4f9;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 40px 20px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0 0 10px 0;
                    font-size: 2.5rem;
                }}
                .header p {{
                    margin: 0;
                    font-size: 1.1rem;
                    opacity: 0.9;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .controls {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .search-bar {{
                    display: flex;
                    gap: 15px;
                    margin-bottom: 20px;
                    flex-wrap: wrap;
                }}
                .search-input {{
                    flex: 1;
                    min-width: 300px;
                    padding: 12px;
                    font-size: 16px;
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                }}
                .filter-buttons {{
                    display: flex;
                    gap: 10px;
                    flex-wrap: wrap;
                    margin-bottom: 15px;
                }}
                .filter-btn {{
                    padding: 8px 16px;
                    border: 2px solid #667eea;
                    background: white;
                    color: #667eea;
                    border-radius: 20px;
                    cursor: pointer;
                    font-size: 0.9rem;
                    transition: all 0.3s ease;
                }}
                .filter-btn:hover, .filter-btn.active {{
                    background: #667eea;
                    color: white;
                }}
                .btn-download {{
                    background: #28a745;
                    color: white;
                    padding: 12px 24px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: bold;
                }}
                .article-card {{
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                    margin-bottom: 20px;
                    padding: 20px;
                    transition: transform 0.3s, box-shadow 0.3s;
                }}
                .article-card:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 15px rgba(0, 0, 0, 0.15);
                }}
                .article-title {{
                    font-size: 1.3rem;
                    color: #2c3e50;
                    margin: 0 0 15px 0;
                    line-height: 1.4;
                }}
                .article-meta {{
                    display: flex;
                    gap: 15px;
                    margin-bottom: 15px;
                    flex-wrap: wrap;
                }}
                .tab-badge {{
                    background: #667eea;
                    color: white;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 0.8rem;
                    font-weight: bold;
                }}
                .publisher, .date, .word-count {{
                    color: #7f8c8d;
                    font-size: 0.9rem;
                }}
                .article-preview p {{
                    color: #34495e;
                    line-height: 1.6;
                    margin-bottom: 15px;
                }}
                .expand-btn {{
                    background: #3498db;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 0.9rem;
                }}
                .expand-btn:hover {{
                    background: #2980b9;
                }}
                .article-full {{
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 1px solid #ecf0f1;
                }}
                .summary-content {{
                    color: #2c3e50;
                    line-height: 1.6;
                    margin-bottom: 20px;
                }}
                .source-link {{
                    background: #27ae60;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 6px;
                    text-decoration: none;
                    font-size: 0.9rem;
                }}
                .source-link:hover {{
                    background: #229954;
                }}
                .stats {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                    text-align: center;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .stats h3 {{
                    margin: 0 0 15px 0;
                    color: #2c3e50;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                    gap: 20px;
                }}
                .stat-item {{
                    color: #7f8c8d;
                }}
                .stat-number {{
                    font-size: 1.8rem;
                    font-weight: bold;
                    color: #667eea;
                    display: block;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 B2B Vault Analysis</h1>
                <p>Comprehensive analysis of {len(processed_articles)} B2B articles with AI insights</p>
            </div>
            
            <div class="container">
                <div class="stats">
                    <h3>📈 Analysis Overview</h3>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <span class="stat-number">{len(processed_articles)}</span>
                            <div>Articles Analyzed</div>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">{len(set(a.get('tab', 'Unknown') for a in processed_articles))}</span>
                            <div>Categories</div>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">{len(set(a.get('publisher', 'Unknown') for a in processed_articles))}</span>
                            <div>Publishers</div>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">{sum(len(a.get('summary', '').split()) for a in processed_articles)}</span>
                            <div>Total Insights</div>
                        </div>
                    </div>
                </div>
                
                <div class="controls">
                    <div class="search-bar">
                        <input type="text" class="search-input" placeholder="🔍 Search articles by title, content, publisher, or category..." onkeyup="searchArticles()">
                        {pdf_link}
                    </div>
                    
                    <div class="filter-buttons">
                        <button class="filter-btn active" onclick="filterByTag('all')">All Articles</button>
                        {' '.join([f'<button class="filter-btn" onclick="filterByTag(\'{tag}\')">{tag}</button>' for tag in sorted(set(a.get('tab', 'Unknown') for a in processed_articles))])}
                    </div>
                </div>
                
                <div class="articles-container">
                    {articles_html}
                </div>
            </div>

            <script>
                let currentFilter = 'all';
                
                function toggleArticle(index) {{
                    const fullDiv = document.getElementById('full-' + index);
                    const btn = event.target;
                    
                    if (fullDiv.style.display === 'none') {{
                        fullDiv.style.display = 'block';
                        btn.textContent = 'Show Less';
                    }} else {{
                        fullDiv.style.display = 'none';
                        btn.textContent = 'Read Full Summary';
                    }}
                }}
                
                function filterByTag(tag) {{
                    currentFilter = tag;
                    
                    // Update button states
                    document.querySelectorAll('.filter-btn').forEach(btn => {{
                        btn.classList.remove('active');
                    }});
                    event.target.classList.add('active');
                    
                    // Filter articles
                    const articles = document.querySelectorAll('.article-card');
                    articles.forEach(article => {{
                        const articleTag = article.querySelector('.tab-badge').textContent;
                        if (tag === 'all' || articleTag === tag) {{
                            article.style.display = 'block';
                        }} else {{
                            article.style.display = 'none';
                        }}
                    }});
                    
                    // Clear search when filtering
                    document.querySelector('.search-input').value = '';
                }}
                
                function searchArticles() {{
                    const searchTerm = document.querySelector('.search-input').value.toLowerCase();
                    const articles = document.querySelectorAll('.article-card');
                    
                    articles.forEach(article => {{
                        const title = article.querySelector('.article-title').textContent.toLowerCase();
                        const content = article.textContent.toLowerCase();
                        const tag = article.querySelector('.tab-badge').textContent;
                        
                        const matchesSearch = searchTerm === '' || content.includes(searchTerm);
                        const matchesFilter = currentFilter === 'all' || tag === currentFilter;
                        
                        if (matchesSearch && matchesFilter) {{
                            article.style.display = 'block';
                        }} else {{
                            article.style.display = 'none';
                        }}
                    }});
                }}
            </script>
        </body>
        </html>
        """
        
        # Save the HTML file
        html_path = os.path.join(website_dir, "index.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Website generated: {html_path}")
        if preview:
            print(f"   ✅ Website saved to: {html_path}")
        
        return html_path

# Command line interface for comprehensive scraping
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='B2B Vault Comprehensive Scraper - Scrapes ALL articles')
    parser.add_argument('--preview', action='store_true', help='Show preview output')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of articles to process (for testing)')
    args = parser.parse_args()
    
    print("🚀 Starting COMPREHENSIVE B2B Vault scraping (ALL articles)")
    print("📊 This will scrape every available article from B2B Vault")
    
    # Initialize and run comprehensive scraping
    agent = B2BVaultAgent(max_workers=5)
    
    # Collect ALL articles from ALL tabs
    print(f"\n📑 Collecting articles from ALL categories...")
    all_articles = agent.scrape_all_articles(preview=args.preview)
    
    if not all_articles:
        print("❌ No articles found")
        exit(1)
    
    # Apply limit if specified (for testing)
    if args.limit:
        all_articles = all_articles[:args.limit]
        print(f"⚠️ Limited to {len(all_articles)} articles for testing")
    
    print(f"\n📊 Total articles collected: {len(all_articles)}")
    
    # Process ALL articles
    print(f"\n🤖 Processing ALL articles with AI analysis...")
    processed_articles = agent.process_multiple_articles_parallel(all_articles, preview=args.preview)
    print(f"   Successfully processed: {len(processed_articles)} articles")
    
    if processed_articles:
        # Generate comprehensive outputs
        print(f"\n📄 Generating comprehensive PDF report...")
        pdf_path = agent.generate_comprehensive_pdf_report(processed_articles, preview=args.preview)
        
        print(f"\n🌐 Generating advanced website with filtering...")
        website_path = agent.generate_advanced_website(processed_articles, pdf_path, preview=args.preview)
        
        print(f"\n✅ Comprehensive scraping complete!")
        print(f"   📊 Total articles: {len(all_articles)}")
        print(f"   🤖 Processed articles: {len(processed_articles)}")
        print(f"   📂 Categories: {len(set(a['tab'] for a in all_articles))}")
        print(f"   📰 Publishers: {len(set(a['publisher'] for a in all_articles))}")
        print(f"   📄 PDF: {pdf_path}")
        print(f"   🌐 Website: {website_path}")
    else:
        print("❌ No articles were successfully processed")
