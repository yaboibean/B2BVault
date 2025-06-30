import os
import time
import requests
import logging
from bs4 import BeautifulSoup
from apscheduler.schedulers.blocking import BlockingScheduler
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from tenacity import retry, wait_exponential, stop_after_attempt, wait_fixed
from weasyprint import HTML
from tqdm import tqdm
import csv
import json
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional
import random
import concurrent.futures
import asyncio
from playwright.async_api import async_playwright

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Config
PERPLEXITY_API_KEY = "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"
BASE_URL = "https://www.theb2bvault.com/"
REPORT_FILENAME = "b2b_vault_report.pdf"

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def safe_get_title(card):
    """Safely extract title from a card element with retries."""
    try:
        all_text = card.inner_text()
        
        # Debug: Print the raw text to see what we're working with
        # print(f"DEBUG - Raw card text: {all_text[:200]}...")
        
        if "Published by:" in all_text:
            # Split on "Published by:" to get the part after publisher info
            parts = all_text.split("Published by:", 1)
            if len(parts) == 2:
                after_published = parts[1].strip()
                
                # Common publishers - extract text after these
                publishers = [
                    "ProductLed", "Growth Unhinged", "Gong", "Klue", "April Dunford", 
                    "Navattic", "Chili Piper", "Trigify", "HeyReach", "MRR Unlocked",
                    "HockeyStack", "Crossbeam", "UserGems", "The CMO", "Marketing Week",
                    "Demand Curve"
                ]
                
                for publisher in publishers:
                    if after_published.startswith(publisher):
                        # Get text after publisher name
                        title_text = after_published[len(publisher):].strip()
                        
                        # Clean up - remove button text and descriptions
                        if "Read Full Article" in title_text:
                            title_text = title_text.split("Read Full Article")[0].strip()
                        if "Read Summary" in title_text:
                            title_text = title_text.split("Read Summary")[0].strip()
                        
                        # Look for sentence boundaries to extract just the title
                        sentences = title_text.split('.')
                        if sentences and len(sentences[0].strip()) > 10:
                            potential_title = sentences[0].strip()
                            if len(potential_title) < 200:  # Reasonable title length
                                return potential_title
                        
                        # Fallback: take first reasonable chunk
                        words = title_text.split()
                        if len(words) >= 4:
                            # Take first 10-15 words as title
                            title_words = words[:15]
                            title_candidate = ' '.join(title_words)
                            if len(title_candidate) > 20 and len(title_candidate) < 200:
                                return title_candidate
                
                # If no publisher match, try to extract title from the text after "Published by:"
                # Skip the first word (likely publisher) and look for title patterns
                words = after_published.split()
                if len(words) > 3:
                    # Skip first 1-2 words (publisher), then look for title
                    for start_idx in range(1, min(3, len(words))):
                        title_words = []
                        for word in words[start_idx:]:
                            if word.lower() in ['read', 'make', 'most', 'many', 'want', 'looking', 'if', 'in', 'this']:
                                break
                            title_words.append(word)
                            if len(' '.join(title_words)) > 60:  # Reasonable title length
                                break
                        
                        if len(title_words) >= 4:
                            title_candidate = ' '.join(title_words)
                            if len(title_candidate) > 15 and len(title_candidate) < 200:
                                return title_candidate
        
        # Last resort: try to find text that looks like a title in the full text
        lines = all_text.split('\n')
        for line in lines:
            line = line.strip()
            # Skip short lines, tags, and button text
            if (len(line) > 20 and len(line) < 150 and 
                not line.lower().startswith(('copy', 'positioning', 'sales', 'published by', 'read full', 'read summary')) and
                not line.lower() in ['read full article', 'read summary']):
                return line
        
        return "Untitled Article"

    except Exception as e:
        print(f"DEBUG TITLE - Exception: {e}")
        return "Untitled Article"

def safe_get_publisher(card):
    """Safely extract publisher from a card element."""
    try:
        all_text = card.inner_text()
        
        if "Published by:" in all_text:
            after_published = all_text.split("Published by:", 1)[1].strip()
            
            # Known publishers
            publishers = [
                "ProductLed", "Growth Unhinged", "Gong", "Klue", "April Dunford", 
                "Navattic", "Chili Piper", "Trigify", "HeyReach", "MRR Unlocked",
                "HockeyStack", "Crossbeam", "UserGems", "The CMO", "Marketing Week",
                "Demand Curve"
            ]
            
            for publisher in publishers:
                if after_published.startswith(publisher):
                    return publisher
            
            # Fallback: take first word(s) as publisher
            words = after_published.split()
            if len(words) >= 1:
                if len(words) >= 2 and words[1][0].isupper():  # Two capitalized words
                    return f"{words[0]} {words[1]}"
                else:
                    return words[0]
        
        return "Unknown Publisher"
        
    except Exception as e:
        print(f"DEBUG PUBLISHER - Exception: {e}")
        return "Unknown Publisher"
        
    except Exception as e:
        print(f"DEBUG PUBLISHER - Exception: {e}")
        pass
    
    return "Unknown Publisher"

class B2BVaultAgent:
    """
    An intelligent agent that scrapes B2B Vault, analyzes content, and generates reports.
    """
    
    def __init__(self, output_dir: str = "scraped_data", tabs_to_search: List[str] = ["Sales"], max_workers: int = 5):
        """Initialize the B2B Vault agent."""
        self.output_dir = output_dir
        self.tabs_to_search = tabs_to_search
        self.max_workers = max_workers  # For parallel processing
        os.makedirs(output_dir, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'{output_dir}/agent.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def navigate_to_tab_and_get_articles(self, tab_name: str, preview: bool = False):
        """Navigate to specified tab and collect article URLs with speed optimizations."""
        articles = []
        seen_urls = set()
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=not preview,
                args=['--disable-blink-features=AutomationControlled', '--no-sandbox']  # Faster browser
            )
            page = browser.new_page()
            
            try:
                self.logger.info(f"Navigating to B2B Vault - {tab_name} tab")
                if preview:
                    print(f"🌐 Opening {BASE_URL} - {tab_name} tab")
                page.goto(BASE_URL, timeout=20000)  # Further reduced timeout
                
                # Skip cookie handling for speed
                page.wait_for_timeout(500)  # Minimal wait
                
                # Navigate to specified tab
                self.logger.info(f"Clicking on {tab_name} tab")
                if preview:
                    print(f"📑 Navigating to {tab_name} tab")
                page.wait_for_selector(f"a[data-w-tab='{tab_name}']", timeout=5000)
                tab = page.locator(f"a[data-w-tab='{tab_name}']")
                tab.click()
                page.wait_for_timeout(1000)  # Reduced wait time
                
                # Faster, aggressive scrolling
                self.logger.info("Loading articles by scrolling")
                if preview:
                    print("📜 Fast scrolling to load articles...")
                
                # Scroll to bottom immediately, then check if more content loads
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)  # Wait for dynamic content
                
                # One more scroll to catch any remaining content
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1000)
                
                if preview:
                    print("   ✅ Fast scroll completed")
                
                # Process cards with optimized extraction
                cards = page.locator("div.w-dyn-item")
                count = cards.count()
                self.logger.info(f"Found {count} article cards")
                if preview:
                    print(f"🔍 Found {count} article cards, fast filtering for {tab_name} articles...")
                
                # Process all cards at once without batching for speed
                for i in range(count):
                    try:
                        card = cards.nth(i)
                        
                        # Fast tag checking
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
                        
                        # Fast URL extraction
                        href = None
                        try:
                            buttons = card.locator("a.button-primary-small").all()
                            if buttons:
                                href = buttons[0].get_attribute("href")
                        except:
                            continue
                        
                        # Quick duplicate check and add
                        if href and href.startswith("http") and href not in seen_urls:
                            seen_urls.add(href)
                            
                            # Fast title/publisher extraction
                        try:
                            title = safe_get_title(card)
                            publisher = safe_get_publisher(card)
                            
                            # Debug output
                            if preview and len(articles) < 5:  # Show first 5 for debugging
                                print(f"   DEBUG - Extracted title: '{title}'")
                                print(f"   DEBUG - Extracted publisher: '{publisher}'")
                        except Exception as e:
                            title = f"Article {len(articles) + 1} from {tab_name}"
                            publisher = "Unknown Publisher"
                            if preview:
                                print(f"   DEBUG - Title extraction failed: {e}")

                            
                            articles.append({
                                "title": title,
                                "publisher": publisher,
                                "url": href,
                                "tab": tab_name,
                                "scraped_at": time.strftime('%Y-%m-%d %H:%M:%S')
                            })
                            
                            if preview and len(articles) <= 10:  # Show fewer for speed
                                print(f"   📰 Article {len(articles)}: {title[:40]}...")
                    except:
                        continue
                
                self.logger.info(f"Collected {len(articles)} unique {tab_name} articles")
                if preview:
                    print(f"✅ Collected {len(articles)} unique {tab_name} articles")
                
            except Exception as e:
                self.logger.error(f"Error navigating to {tab_name} tab: {e}")
                raise
            finally:
                browser.close()
        
        return articles

    async def scrape_article_content_async(self, article_url: str, browser_context) -> str:
        """Async version of article content scraping."""
        try:
            page = await browser_context.new_page()
            await page.goto(article_url, timeout=20000)  # Faster timeout
            await page.wait_for_load_state("domcontentloaded")  # Don't wait for full load
            
            # Get content faster using async
            content = await page.content()
            await page.close()
            
            # Parse with BeautifulSoup (same logic as before)
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

    async def process_articles_batch_async(self, articles_batch: List[Dict], preview: bool = False) -> List[Dict]:
        """Process a batch of articles asynchronously with parallel scraping and API calls."""
        processed_articles = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            
            # Scrape all articles in parallel
            scrape_tasks = []
            for article in articles_batch:
                task = self.scrape_article_content_async(article['url'], context)
                scrape_tasks.append((article, task))
            
            # Wait for all scraping to complete
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
        
        # Now process Perplexity API calls in parallel using ThreadPoolExecutor
        if scraped_results:
            def process_single_article(article_content_pair):
                article, content = article_content_pair
                try:
                    summary = self.send_to_perplexity(content, preview=False)
                    return {
                        **article,
                        'content': content,
                        'summary': summary
                    }
                except Exception as e:
                    self.logger.error(f"Error processing article '{article['title']}': {e}")
                    return None
            
            # Use ThreadPoolExecutor for parallel API calls
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(self.max_workers, 5)) as executor:
                results = list(executor.map(process_single_article, scraped_results))
                processed_articles = [r for r in results if r is not None]
        
        return processed_articles

    def process_multiple_articles_parallel(self, articles: List[Dict], preview: bool = False) -> List[Dict]:
        """Process multiple articles using parallel execution with optimized batching."""
        if preview:
            print(f"\n🔄 Processing {len(articles)} articles in parallel...")
        
        # Smaller batches for better parallelization
        batch_size = min(self.max_workers, 8)  # Smaller batches
        article_batches = [articles[i:i + batch_size] for i in range(0, len(articles), batch_size)]
        
        all_processed_articles = []
        
        for batch_idx, batch in enumerate(article_batches):
            if preview:
                print(f"\n📦 Processing batch {batch_idx + 1}/{len(article_batches)} ({len(batch)} articles)...")
            
            # Run async batch processing
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
            
            # No delay between batches since we're using smaller batches
        
        return all_processed_articles

    def send_to_perplexity(self, article_content: str, preview: bool = False) -> str:
        """Send article content to Perplexity API with faster settings and strict TL;DR ending."""
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
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
                h1 {{
                    color: #2c3e50;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
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
                    <button class="expand-btn" onclick="toggleArticle({i})">Read Full Analysis</button>
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
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>B2B Vault Analysis Dashboard</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                
                .header {{
                    text-align: center;
                    color: white;
                    margin-bottom: 40px;
                    padding: 40px 20px;
                }}
                
                .header h1 {{
                    font-size: 3rem;
                    margin-bottom: 10px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }}
                
                .header p {{
                    font-size: 1.2rem;
                    opacity: 0.9;
                }}
                
                .stats {{
                    display: flex;
                    justify-content: center;
                    gap: 30px;
                    margin: 30px 0;
                    flex-wrap: wrap;
                }}
                
                .stat-card {{
                    background: rgba(255,255,255,0.1);
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                    color: white;
                    backdrop-filter: blur(10px);
                }}
                
                .stat-number {{
                    font-size: 2rem;
                    font-weight: bold;
                    display: block;
                }}
                
                .search-box {{
                    margin: 30px 0;
                    text-align: center;
                }}
                
                .search-input {{
                    padding: 12px 20px;
                    font-size: 16px;
                    border: none;
                    border-radius: 25px;
                    width: 300px;
                    max-width: 90%;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                
                .articles-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                    gap: 30px;
                    margin-top: 30px;
                }}
                
                .article-card {{
                    background: white;
                    border-radius: 15px;
                    padding: 25px;
                    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                    border-left: 5px solid #667eea;
                }}
                
                .article-card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 15px 35px rgba(0,0,0,0.15);
                }}
                
                .article-title {{
                    color: #2c3e50;
                    margin-bottom: 15px;
                    font-size: 1.3rem;
                    line-height: 1.4;
                }}
                
                .article-meta {{
                    display: flex;
                    gap: 10px;
                    margin-bottom: 15px;
                    flex-wrap: wrap;
                }}
                
                .tab-badge {{
                    background: #667eea;
                    color: white;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 0.8rem;
                    font-weight: bold;
                }}
                
                .date, .word-count, .publisher {{
                    color: #666;
                    font-size: 0.9rem;
                    padding: 4px 8px;
                    background: #f8f9fa;
                    border-radius: 15px;
                }}
                
                .article-preview p {{
                    margin-bottom: 15px;
                    color: #555;
                    line-height: 1.6;
                }}
                
                .expand-btn, .source-link {{
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 25px;
                    cursor: pointer;
                    text-decoration: none;
                    display: inline-block;
                    transition: background 0.3s ease;
                    font-size: 0.9rem;
                }}
                
                .expand-btn:hover, .source-link:hover {{
                    background: #5a6fd8;
                }}
                
                .article-full {{
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                }}
                
                .summary-content {{
                    margin-bottom: 20px;
                    line-height: 1.7;
                    color: #444;
                }}
                
                .article-link {{
                    text-align: center;
                }}
                
                .footer {{
                    text-align: center;
                    color: white;
                    margin-top: 50px;
                    padding: 20px;
                    opacity: 0.8;
                }}
                
                @media (max-width: 768px) {{
                    .articles-grid {{
                        grid-template-columns: 1fr;
                    }}
                    
                    .header h1 {{
                        font-size: 2rem;
                    }}
                    
                    .stats {{
                        gap: 15px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>B2B Vault Analysis Dashboard</h1>
                    <p>B2B Vault articles summaries</p>
                    
                    <div class="stats">
                        <div class="stat-card">
                            <span class="stat-number">{len(processed_articles)}</span>
                            <span>Articles Analyzed</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-number">{sum(len(a['summary'].split()) for a in processed_articles):,}</span>
                            <span>Total Words</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-number">{len(set(a['tab'] for a in processed_articles))}</span>
                            <span>Categories</span>
                        </div>
                    </div>
                    
                    <div class="search-box">
                        <input type="text" class="search-input" placeholder="Search articles..." onkeyup="searchArticles()">
                    </div>
                </div>
                
                <div class="articles-grid" id="articles-grid">
                    {articles_html}
                </div>
                
                <div class="footer">
                    <p>Generated on {time.strftime('%Y-%m-%d %H:%M:%S')} | Powered by Perplexity AI</p>
                    {f'''<div style="margin-top: 15px;">
                        <a href="../{os.path.basename(pdf_path)}" 
                           class="source-link" 
                           download
                           style="background: #e74c3c; padding: 12px 24px; font-size: 1rem; text-decoration: none; border-radius: 30px; display: inline-block; margin: 10px;">
                           📄 Download PDF Report
                        </a>
                    </div>''' if pdf_path and os.path.exists(pdf_path) else ''}
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
                        btn.textContent = 'Read Full Analysis';
                    }}
                }}
                
                function searchArticles() {{
                    const searchTerm = document.querySelector('.search-input').value.toLowerCase();
                    const articles = document.querySelectorAll('.article-card');
                    
                    articles.forEach(article => {{
                        const title = article.querySelector('.article-title').textContent.toLowerCase();
                        const content = article.textContent.toLowerCase();
                        
                        if (title.includes(searchTerm) || content.includes(searchTerm)) {{
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
        
        try:
            # Save the website
            website_path = os.path.join(website_dir, "index.html")
            with open(website_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # Generate a simple launcher script
            launcher_script = f"""#!/usr/bin/env python3
import os
import http.server
import socketserver
import webbrowser
import time

def start_server():
    website_dir = r"{website_dir}"
    PORT = 8000
    
    if not os.path.exists(website_dir):
        print("❌ Website directory not found!")
        return
        
    os.chdir(website_dir)
    Handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"🌐 B2B Vault Analysis Website")
            print(f"🚀 Server running at http://localhost:{{PORT}}")
            print("📱 Opening in your browser...")
            print("⏹️  Press Ctrl+C to stop the server")
            
            time.sleep(1)
            webbrowser.open(f'http://localhost:{{PORT}}')
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\\n✅ Server stopped.")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {{PORT}} is already in use. Try a different port or stop the existing server.")
        else:
            print(f"❌ Error starting server: {{e}}")

if __name__ == "__main__":
    start_server()
"""
            
            server_path = os.path.join(website_dir, "start_server.py")
            with open(server_path, "w", encoding="utf-8") as f:
                f.write(launcher_script)
            
            # Make server script executable (Unix/Mac)
            try:
                os.chmod(server_path, 0o755)
            except:
                pass  # Windows doesn't support chmod
            
            if preview:
                print(f"   ✅ Website generated: {website_path}")
                print(f"   🚀 Server script: {server_path}")
                print(f"   💡 To view the website, run:")
                print(f"       python3 start_website.py")
                print(f"   Or navigate to the website folder and run:")
                print(f"       python3 start_server.py")
            
            return website_path
            
        except Exception as e:
            self.logger.error(f"Error generating website: {e}")
            raise

    def debug_card_structure(self, preview: bool = False):
        """Debug method to understand the card structure on B2B Vault."""
        if not preview:
            return
            
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # Always show browser for debugging
            page = browser.new_page()
            
            try:
                print("🔍 DEBUG: Analyzing B2B Vault card structure...")
                page.goto(BASE_URL, timeout=60000)
                
                # Navigate to Sales tab
                page.wait_for_selector("a[data-w-tab='Sales']", timeout=10000)
                sales_tab = page.locator("a[data-w-tab='Sales']")
                sales_tab.click()
                page.wait_for_timeout(3000)
                
                # Get first few cards
                cards = page.locator("div.w-dyn-item")
                count = min(cards.count(), 10)  # Look at first 10 cards
                
                print(f"🔍 DEBUG: Found {cards.count()} total cards, analyzing first {count}...")
                
                for i in range(count):
                    card = cards.nth(i)
                    print(f"\n--- CARD {i} DEBUG ---")
                    
                    # Try to extract all text from the card
                    try:
                        card_html = card.inner_html()
                        with open(f"{self.output_dir}/debug_card_{i}.html", "w", encoding="utf-8") as f:
                            f.write(f"<!-- Card {i} HTML -->\n{card_html}\n")
                        tag_selectors = [
                        "[class*='tag']",
                        "[class*='category']",
                        "div[class*='text']"
                    ]
                    
                        for selector in tag_selectors:
                            try:
                                elements = card.locator(selector).all()
                                if elements:
                                    print(f"Selector '{selector}' found {len(elements)} elements:")
                                    for j, elem in enumerate(elements):
                                        text = elem.inner_text().strip()
                                        if text:
                                            print(f"  Element {j}: '{text}'")
                                else:
                                    print(f"Selector '{selector}': No elements found")
                            except Exception as e:
                                print(f"Selector '{selector}': Error - {e}")
                        
                        # Try different title selectors
                        title_selectors = [
                            "div.h6-heading",
                            ".h6-heading",
                            "h1", "h2", "h3", "h4", "h5", "h6",
                            "[class*='heading']",
                            "[class*='title']"
                        ]
                        
                        print("TITLE EXTRACTION ATTEMPTS:")
                        for selector in title_selectors:
                            try:
                                elements = card.locator(selector).all()
                                if elements:
                                    print(f"Title selector '{selector}' found {len(elements)} elements:")
                                    for j, elem in enumerate(elements):
                                        text = elem.inner_text().strip()
                                        if text:
                                            print(f"  Title element {j}: '{text[:100]}...'")
                            except Exception as e:
                                print(f"Title selector '{selector}': Error - {e}")
                        
                        # Try different publisher selectors
                        publisher_selectors = [
                            ".w-layout-grid.grid-2 .text-block-5",
                            ".text-block-5",
                            "[class*='grid'] [class*='text-block']",
                            "div:has-text('Published by:')",
                            "[class*='publisher']",
                            "[class*='author']"
                        ]
                        
                        print("PUBLISHER EXTRACTION ATTEMPTS:")
                        for selector in publisher_selectors:
                            try:
                                elements = card.locator(selector).all()
                                if elements:
                                    print(f"Publisher selector '{selector}' found {len(elements)} elements:")
                                    for j, elem in enumerate(elements):
                                        text = elem.inner_text().strip()
                                        if text:
                                            print(f"  Publisher element {j}: '{text}'")
                            except Exception as e:
                                print(f"Publisher selector '{selector}': Error - {e}")
                        
                        print("--- END CARD DEBUG ---\n")
                    except Exception as e:
                        print(f"Could not get card HTML or debug info: {e}")
                
            except Exception as e:
                print(f"DEBUG ERROR: {e}")
            finally:
                input("Press Enter to close browser...")  # Wait for user
                browser.close()

    def run_comprehensive_analysis(self, preview: bool = False):
        """Run comprehensive analysis for all specified tabs with speed optimizations."""
        try:
            start_time = time.time()
            self.logger.info("Starting comprehensive B2B Vault analysis workflow")
            if preview:
                print("\n" + "="*70)
                print("🚀 B2B VAULT COMPREHENSIVE ANALYSIS WORKFLOW STARTING")
                print(f"📑 Tabs to search: {', '.join(self.tabs_to_search)}")
                print(f"⚡ Max parallel workers: {self.max_workers}")
                print("="*70)
            
            all_articles = []
            
            # Step 1: Collect articles from all specified tabs
            for tab in self.tabs_to_search:
                if preview:
                    print(f"\n📋 STEP 1.{self.tabs_to_search.index(tab)+1}: Collecting {tab} Articles")
                    print("-" * 50)
                
                tab_articles = self.navigate_to_tab_and_get_articles(tab, preview)
                all_articles.extend(tab_articles)
                
                if preview:
                    print(f"✅ Found {len(tab_articles)} articles in {tab} tab")
            
            if not all_articles:
                self.logger.error("No articles found in any specified tabs")
                return None
            
            if preview:
                print(f"\n📊 TOTAL UNIQUE ARTICLES FOUND: {len(all_articles)}")
                print("-" * 50)
                for i, article in enumerate(all_articles[:15]):
                    print(f"{i+1}. [{article['tab']}] {article['title'][:60]}{'...' if len(article['title']) > 60 else ''}")
                if len(all_articles) > 15:
                    print(f"... and {len(all_articles) - 15} more articles")
            
            # Step 2: Process all articles in parallel
            if preview:
                print(f"\n🔄 STEP 2: Processing All Articles (Parallel)")
                print("-" * 50)
            
            processed_articles = self.process_multiple_articles_parallel(all_articles, preview)
            
            if not processed_articles:
                self.logger.error("No articles were successfully processed")
                return None
            
            # Step 3: Generate comprehensive PDF report
            if preview:
                print(f"\n📄 STEP 3: Generating Comprehensive PDF Report")
                print("-" * 50)

            pdf_path = self.generate_comprehensive_pdf_report(processed_articles, preview)

            # Step 4: Generate website
            if preview:
                print(f"\n🌐 STEP 4: Generating Website")
                print("-" * 50)
            
            website_path = self.generate_website(processed_articles, pdf_path, preview)

            total_time = time.time() - start_time
            if preview:
                print(f"\n✅ COMPREHENSIVE ANALYSIS COMPLETED!")
                print("="*70)
                print(f"📰 Total Articles Processed: {len(processed_articles)}")
                print(f"📄 Comprehensive PDF Report: {pdf_path}")
                print(f"🌐 Website: {website_path}")
                print(f"📊 Total Analysis: {sum(len(a['summary'].split()) for a in processed_articles)} words")
                print(f"⏱️  Total Time: {total_time:.1f} seconds")
                print(f"⚡ Speed: {len(processed_articles)/total_time:.1f} articles/second")
                print("="*70)

            return {
                "processed_articles": len(processed_articles),
                "total_articles": len(all_articles),
                "pdf_path": pdf_path,
                "website_path": website_path,
                "articles": processed_articles,
                "total_time": total_time
            }

        except Exception as e:
            self.logger.error(f"Error in comprehensive analysis: {e}")
            if preview:
                print(f"\n❌ ERROR: {e}")
            return None

def start_scheduler():
    """Start the scheduled execution of the agent."""
    agent = B2BVaultAgent()
    scheduler = BlockingScheduler()
    
    # Run every hour
    scheduler.add_job(
        func=agent.run_full_analysis,
        trigger='interval',
        hours=1,
        id='b2b_vault_analysis'
    )
    
    print("Scheduler started. Agent will run every hour.")
    print("Press Ctrl+C to stop.")
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("Scheduler stopped.")

if __name__ == "__main__":
    # Optimized settings for speed
    tabs_to_search = ["Sales"]
    agent = B2BVaultAgent(tabs_to_search=tabs_to_search, max_workers=10)  # More workers
    
    # Option 1: Just start the website server for existing data
    # agent.start_website_server(preview=True)
    
    # Option 2: Enable debug mode
    # agent.debug_card_structure(preview=True)
    
    # Option 3: Run full comprehensive analysis
    result = agent.run_comprehensive_analysis(preview=True)
    
    if result:
        print(f"✅ Comprehensive analysis complete!")
        print(f"📊 {result['processed_articles']}/{result['total_articles']} articles successfully processed")
        print(f"📄 PDF saved to: {result['pdf_path']}")
        print(f"🌐 Website: {result['website_path']}")
    else:
        print("❌ Analysis failed. Check logs for details.")
    
    # Uncomment the next line if you want to start the scheduler after the analysis
    # start_scheduler()
