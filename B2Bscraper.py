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
