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
    
    def __init__(self, output_dir: str = "scraped_data", tabs_to_search: List[str] = ["Sales"], max_workers: int = 5):
        self.output_dir = output_dir
        self.tabs_to_search = tabs_to_search
        self.max_workers = max_workers
        os.makedirs(output_dir, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def navigate_to_tab_and_get_articles(self, tab_name: str, preview: bool = False):
        """Navigate to tab and collect article URLs."""
        articles = []
        seen_urls = set()
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=not preview)
            page = browser.new_page()
            
            try:
                if preview:
                    print(f"🌐 Opening {BASE_URL} - {tab_name} tab")
                
                page.goto(BASE_URL, timeout=20000)
                page.wait_for_timeout(500)
                
                # Navigate to tab
                page.wait_for_selector(f"a[data-w-tab='{tab_name}']", timeout=5000)
                tab = page.locator(f"a[data-w-tab='{tab_name}']")
                tab.click()
                page.wait_for_timeout(1000)
                
                # Fast scroll to load content
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1000)
                
                # Process cards
                cards = page.locator("div.w-dyn-item")
                count = cards.count()
                
                if preview:
                    print(f"🔍 Found {count} cards, filtering for {tab_name} articles...")
                
                for i in range(count):
                    try:
                        card = cards.nth(i)
                        
                        # Check if article matches tab
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
                            
                            if preview and len(articles) <= 10:
                                print(f"   📰 Article {len(articles)}: {title[:40]}...")
                    except Exception as e:
                        if preview:
                            print(f"   ⚠️ Error processing card {i}: {e}")
                        continue
                
                if preview:
                    print(f"✅ Collected {len(articles)} unique {tab_name} articles")
                
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
            "Content-Type": "application/json"
        }
        
        # Stronger instructions for TL;DR
        prompt = f"""
        Analyze this B2B sales article and provide:
        1. A short 1-sentence TL;DR at the very top. Each sentence must be complete, self-contained, and end with a period or other proper punctuation. it should be around 40 words.
        2. 3-5 key takeaways
        3. Notable companies/technologies
        4. 3-5 actionable recommendations for B2B sales

        Do not use any formatting (no bold, italics, or markdown). Do not mention the prompt or instructions in your answer.

        Make sure to use indenting to make it the easiest it can be to read.

        NO BOLD OR ITALICS. NO MARKDOWN. NO FORMATTING. JUST TEXT AND SPACING (numbers for lists are fine).
        NO CITATIONS. NO SOURCES. NO REFERENCES. JUST THE CONTENT. JUST PLAIN TEXT, NOTHING MORE -- no bold or italics, no markdown, no formatting, just text and spacing (numbers for lists are fine).

        Article:
         
         {article_content[:4000]}
        """
        
        payload = {
            "model": "sonar",
            "messages": [
                {"role": "system", "content": "You are a B2B sales analyst. For the TL;DR, always write two complete sentences that end with a period or other proper punctuation. Never let a TL;DR sentence trail off or end with '...' or incomplete thoughts. If the model tries to end with '...', finish the sentence properly."},
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

            # --- Post-process TL;DR to remove trailing '...' if present ---
            # Find the TL;DR (first two sentences)
            lines = summary.splitlines()
            if lines and "TL;DR" in lines[0]:
                tldr_line = lines[0]
                # Remove trailing '...' and ensure period
                tldr_line = tldr_line.rstrip('.').rstrip()
                if tldr_line.endswith('..'):
                    tldr_line = tldr_line.rstrip('.')
                if not tldr_line.endswith('.'):
                    tldr_line += '.'
                lines[0] = tldr_line
                summary = "\n".join(lines)
            # --- End post-processing ---

            return summary
            
        except Exception as e:
            self.logger.error(f"Perplexity API error: {e}")
            return "Analysis failed"

    def generate_pdf_report(self, summary: str, article_title: str = "B2B Article Analysis", preview: bool = False):
        """Generate a PDF report from the summary."""
        self.logger.info("Generating PDF report")
        if preview:
            print("📄 Generating PDF report...")
        
        # Precompute summary with line breaks replaced
        summary_html = summary.replace('\n', '<br>')

        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    line-height: 1.6;
                }}
                .header {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .content {{
                    white-space: pre-line;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>B2B Vault Analysis Report</h1>
                <p><strong>Article:</strong> {article_title}</p>
                <p><strong>Generated:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            <div class="content">
                {summary_html}
            </div>
        </body>
        </html>
        """
        
        try:
            # Generate PDF
            output_path = os.path.join(self.output_dir, REPORT_FILENAME)
            HTML(string=html_content).write_pdf(output_path)
            self.logger.info(f"PDF report generated: {output_path}")
            if preview:
                print(f"   ✅ PDF saved to: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generating PDF: {e}")
            raise

    def scrape_article_content(self, article_url: str, preview: bool = False) -> str:
        """Synchronous version of article content scraping for fallback processing."""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                page.goto(article_url, timeout=20000)
                page.wait_for_load_state("domcontentloaded")
                
                # Get content
                content = page.content()
                browser.close()
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract title
                title_selectors = ["h1", ".article-title", ".post-title", "title"]
                title = "Untitled"
                for selector in title_selectors:
                    title_elem = soup.select_one(selector)
                    if title_elem and title_elem.get_text(strip=True):
                        title = title_elem.get_text(strip=True)
                        break
                
                # Extract article body
                body_selectors = [
                    "article", ".article-content", ".post-content", 
                    ".content", "main", ".rich-text"
                ]
                
                body_text = ""
                for selector in body_selectors:
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

    def process_multiple_articles(self, articles: List[Dict], preview: bool = False) -> List[Dict]:
        """Process multiple articles and return their summaries."""
        processed_articles = []
        
        if preview:
            print(f"\n🔄 Processing {len(articles)} articles...")
        
        for i, article in enumerate(articles):
            try:
                if preview:
                    print(f"\n📖 Processing article {i+1}/{len(articles)}: {article['title'][:60]}...")
                
                # Scrape article content
                content = self.scrape_article_content(article['url'], preview=False)  # Disable preview for individual scraping
                
                if not content:
                    self.logger.warning(f"Failed to scrape content for: {article['title']}")
                    continue
                
                # Send to Perplexity for analysis
                if preview:
                    print(f"   🤖 Analyzing with Perplexity AI...")
                summary = self.send_to_perplexity(content, preview=False)
                
                processed_articles.append({
                    **article,
                    'content': content,
                    'summary': summary
                })
                
                if preview:
                    print(f"   ✅ Article {i+1} processed successfully")
                
                # Add a small delay to be respectful to the API
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error processing article '{article['title']}': {e}")
                if preview:
                    print(f"   ❌ Error processing article {i+1}: {e}")
                continue
        
        return processed_articles

    def generate_comprehensive_pdf_report(self, processed_articles: List[Dict], preview: bool = False):
        """Generate a comprehensive PDF report with all processed articles."""
        self.logger.info("Generating comprehensive PDF report")
        if preview:
            print(f"📄 Generating comprehensive PDF report with {len(processed_articles)} articles...")
        
        # Create HTML content for all articles
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
        
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    line-height: 1.6;
                }}
                h1 {{
                    color: #2c3e50;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 15px;
                    text-align: center;
                }}
                h2 {{
                    color: #34495e;
                    border-bottom: 2px solid #ecf0f1;
                    padding-bottom: 10px;
                    margin-top: 30px;
                }}
                h3 {{
                    color: #2980b9;
                    margin-top: 25px;
                }}
                .header {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                    text-align: center;
                }}
                .article-section {{
                    margin-bottom: 40px;
                    padding: 20px;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    background-color: #fafafa;
                }}
                .article-meta {{
                    background-color: #e8f4f8;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .article-meta p {{
                    margin: 5px 0;
                }}
                .article-summary {{
                    background-color: white;
                    padding: 20px;
                    border-radius: 5px;
                    border-left: 4px solid #3498db;
                }}
                .page-break {{
                    page-break-before: always;
                }}
                a {{
                    color: #3498db;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
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
            # Generate PDF
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
        """Generate a static website to display all analyzed articles."""
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
        
        # Generate main HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>B2B Vault Analysis</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f4f4f9;
                }}
                h1 {{
                    text-align: center;
                    color: #333;
                    margin: 20px 0;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .search-bar {{
                    margin-bottom: 30px;
                    display: flex;
                    justify-content: center;
                }}
                .search-input {{
                    width: 100%;
                    max-width: 600px;
                    padding: 10px;
                    font-size: 16px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                }}
                .article-card {{
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                    margin-bottom: 20px;
                    padding: 15px;
                    position: relative;
                    transition: transform 0.3s, box-shadow 0.3s;
                }}
                .article-card:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
                }}
                .article-title {{
                    font-size: 18px;
                    color: #007bff;
                    margin: 0 0 10px 0;
                }}
                .article-meta {{
                    font-size: 14px;
                    color: #666;
                    margin: 0 0 10px 0;
                }}
                .article-preview {{
                    font-size: 16px;
                    color: #333;
                    margin: 0 0 10px 0;
                }}
                .expand-btn {{
                    background-color: #007bff;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 16px;
                }}
                .expand-btn:hover {{
                    background-color: #0056b3;
                }}
                .article-full {{
                    margin-top: 10px;
                    font-size: 16px;
                    color: #333;
                }}
                .article-link {{
                    margin-top: 10px;
                    display: inline-block;
                }}
                .source-link {{
                    background-color: #28a745;
                    color: white;
                    padding: 10px 15px;
                    border-radius: 4px;
                    text-decoration: none;
                }}
                .source-link:hover {{
                    background-color: #218838;
                }}
                .relevance-indicator {{
                    position: absolute;
                    top: 10px;
                    right: 10px;
                    background: rgba(0, 123, 255, 0.1);
                    color: #007bff;
                    padding: 5px 10px;
                    border-radius: 12px;
                    font-size: 0.8rem;
                    font-weight: bold;
                }}
                mark {{
                    background: #fff3cd;
                    padding: 1px 2px;
                    border-radius: 2px;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>B2B Vault Analysis</h1>
                
                <div class="search-bar">
                    <input type="text" class="search-input" placeholder="Search articles by title, publisher, or tab...">
                </div>
                
                <div class="articles-container">
                    {articles_html}
                </div>
            </div>

            <script>
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
                
                // Enhanced fuzzy search with improved scoring
                function fuzzySearch(searchTerm, text) {{
                    const query = searchTerm.toLowerCase();
                    const target = text.toLowerCase();
                    
                    if (target.includes(query)) return 100;
                    
                    const queryWords = query.split(/\s+/).filter(word => word.length > 1);
                    let score = 0;
                    let matches = 0;
                    
                    queryWords.forEach(word => {{
                        if (target.includes(word)) {{
                            matches++;
                            score += 25; // Higher base score for exact word matches
                        }} else {{
                            // Check for partial matches and typos
                            const similarity = calculateSimilarity(word, target);
                            if (similarity > 0.6) {{
                                matches++;
                                score += similarity * 20;
                            }}
                        }}
                    }});
                    
                    // Bonus for multiple word matches
                    if (matches > 1) {{
                        score += matches * 10;
                    }}
                    
                    return score;
                }}
                
                function calculateSimilarity(str1, str2) {{
                    if (str2.includes(str1)) return 0.9;
                    
                    const longer = str1.length > str2.length ? str1 : str2;
                    const shorter = str1.length > str2.length ? str2 : str1;
                    
                    if (longer.length === 0) return 1.0;
                    
                    let matches = 0;
                    for (let i = 0; i < shorter.length; i++) {{
                        if (longer.includes(shorter[i])) matches++;
                    }}
                    
                    return matches / longer.length;
                }}
                
                function searchArticles() {{
                    const searchTerm = document.querySelector('.search-input').value.trim();
                    const articles = document.querySelectorAll('.article-card');
                    
                    if (searchTerm.length === 0) {{
                        // Reset to original state
                        articles.forEach((article, index) => {{
                            article.style.display = 'block';
                            article.style.order = index;
                            article.style.borderLeftColor = '#667eea';
                            article.style.borderLeftWidth = '5px';
                            
                            // Remove highlights and indicators
                            const title = article.querySelector('.article-title');
                            if (title && title.innerHTML !== title.textContent) {{
                                title.innerHTML = title.textContent;
                            }}
                            
                            const indicator = article.querySelector('.relevance-indicator');
                            if (indicator) indicator.remove();
                        }});
                        return;
                    }}
                    
                    const searchResults = [];
                    
                    // Calculate relevance for all articles
                    articles.forEach((article, index) => {{
                        const title = article.querySelector('.article-title').textContent;
                        const content = article.textContent;
                        const publisher = article.querySelector('.publisher')?.textContent || '';
                        const tabBadge = article.querySelector('.tab-badge')?.textContent || '';
                        
                        const titleScore = fuzzySearch(searchTerm, title) * 4;
                        const publisherScore = fuzzySearch(searchTerm, publisher) * 2.5;
                        const tabScore = fuzzySearch(searchTerm, tabBadge) * 2;
                        const contentScore = fuzzySearch(searchTerm, content);
                        
                        const totalScore = titleScore + publisherScore + tabScore + contentScore;
                        
                        searchResults.push({{ 
                            element: article, 
                            score: totalScore, 
                            originalIndex: index 
                        }});
                    }});
                    
                    // Sort by relevance (highest to lowest) - DYNAMIC SORTING
                    searchResults.sort((a, b) => b.score - a.score);
                    
                    let displayOrder = 0;
                    searchResults.forEach((result, rank) => {{
                        if (result.score >= 10) {{
                            result.element.style.display = 'block';
                            result.element.style.order = displayOrder; // Critical for proper ordering
                            displayOrder++;
                            
                            // Dynamic visual feedback
                            if (result.score > 80) {{
                                result.element.style.borderLeftColor = '#27ae60';
                                result.element.style.borderLeftWidth = '6px';
                            }} else if (result.score > 40) {{
                                result.element.style.borderLeftColor = '#f39c12';
                                result.element.style.borderLeftWidth = '5px';
                            }} else {{
                                result.element.style.borderLeftColor = '#667eea';
                                result.element.style.borderLeftWidth = '4px';
                            }}
                            
                            // Highlight search terms
                            const title = result.element.querySelector('.article-title');
                            const originalText = title.textContent;
                            if (searchTerm.length > 1) {{
                                const regex = new RegExp(`(${{searchTerm}})`, 'gi');
                                title.innerHTML = originalText.replace(regex, 
                                    '<mark style="background: #fff3cd; padding: 1px 2px; border-radius: 2px; font-weight: bold;">$1</mark>'
                                );
                            }}
                            
                            // Add rank indicator
                            let indicator = result.element.querySelector('.relevance-indicator');
                            if (!indicator) {{
                                indicator = document.createElement('div');
                                indicator.className = 'relevance-indicator';
                                indicator.style.cssText = `
                                    position: absolute;
                                    top: 10px;
                                    right: 10px;
                                    background: rgba(0,0,0,0.7);
                                    color: white;
                                    padding: 4px 8px;
                                    border-radius: 12px;
                                    font-size: 0.8rem;
                                    font-weight: bold;
                                    z-index: 10;
                                `;
                                result.element.style.position = 'relative';
                                result.element.appendChild(indicator);
                            }}
                            indicator.textContent = `#${{rank + 1}}`;
                            indicator.title = `Relevance: ${Math.round(result.score)}`;
                            
                        } else {
                            result.element.style.display = 'none';
                        }
                    });
                }
