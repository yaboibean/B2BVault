#!/usr/bin/env python3
"""
Memory-efficient version of B2B Vault scraper that processes articles in very small batches
"""
import os
import time
from B2Bscraper import B2BVaultAgent
import gc  # Garbage collection

def run_memory_efficient_scraping():
    """Run scraping with minimal memory usage"""
    print("🚀 Starting MEMORY-EFFICIENT B2B Vault scraping")
    print("💾 This version uses minimal memory and processes articles slowly but safely")
    print("-" * 60)
    
    # Use very conservative settings
    agent = B2BVaultAgent(max_workers=1)  # Single worker only
    
    try:
        # Step 1: Collect articles from homepage (no processing yet)
        print("📑 Collecting articles from homepage...")
        all_articles = agent.scrape_all_articles_from_homepage(preview=True)
        
        if not all_articles:
            print("❌ No articles found")
            return
        
        print(f"\n✅ Found {len(all_articles)} total articles")
        print(f"📂 Categories: {len(set(a['tab'] for a in all_articles))}")
        print(f"📰 Publishers: {len(set(a['publisher'] for a in all_articles))}")
        
        # Step 2: Process in VERY small batches to avoid memory issues
        batch_size = 2  # Process only 2 articles at a time
        processed_articles = []
        
        total_batches = (len(all_articles) + batch_size - 1) // batch_size
        
        print(f"\n🔄 Processing {len(all_articles)} articles in {total_batches} small batches...")
        print("💾 Using minimal memory - this will take longer but won't crash")
        
        for i in range(0, len(all_articles), batch_size):
            batch_num = (i // batch_size) + 1
            batch = all_articles[i:i + batch_size]
            
            print(f"\n📦 Batch {batch_num}/{total_batches}: Processing {len(batch)} articles")
            
            try:
                # Process this small batch
                batch_processed = agent.process_multiple_articles(batch, preview=True)
                processed_articles.extend(batch_processed)
                
                print(f"   ✅ Batch {batch_num} complete: {len(batch_processed)} articles processed")
                print(f"   📊 Total processed so far: {len(processed_articles)}")
                
                # Force garbage collection to free memory
                gc.collect()
                
                # Small delay between batches to be gentle on system
                time.sleep(3)
                
            except Exception as e:
                print(f"   ❌ Batch {batch_num} failed: {e}")
                print(f"   🔄 Continuing with next batch...")
                continue
        
        if not processed_articles:
            print("❌ No articles were successfully processed")
            return
        
        print(f"\n📊 Processing complete: {len(processed_articles)} articles processed successfully")
        
        # Step 3: Generate outputs
        print(f"\n📄 Generating PDF report...")
        try:
            pdf_path = agent.generate_comprehensive_pdf_report(processed_articles, preview=True)
            print(f"✅ PDF generated: {pdf_path}")
        except Exception as e:
            print(f"❌ PDF generation failed: {e}")
            pdf_path = None
        
        print(f"\n🌐 Generating website...")
        try:
            website_path = agent.generate_website(processed_articles, pdf_path, preview=True)
            print(f"✅ Website generated: {website_path}")
        except Exception as e:
            print(f"❌ Website generation failed: {e}")
            website_path = None
        
        # Final summary
        print(f"\n🎉 MEMORY-EFFICIENT SCRAPING COMPLETE!")
        print("=" * 60)
        print(f"📰 Total articles found: {len(all_articles)}")
        print(f"🤖 Articles processed: {len(processed_articles)}")
        print(f"📂 Categories: {len(set(a['tab'] for a in all_articles))}")
        print(f"📰 Publishers: {len(set(a['publisher'] for a in all_articles))}")
        if pdf_path:
            print(f"📄 PDF: {pdf_path}")
        if website_path:
            print(f"🌐 Website: {website_path}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        print("💡 Try reducing batch size further or check your system resources")

def run_test_scraping():
    """Run a test with just a few articles"""
    print("🧪 Running TEST scraping with limited articles...")
    
    agent = B2BVaultAgent(max_workers=1)
    
    try:
        # Collect articles
        all_articles = agent.scrape_all_articles_from_homepage(preview=True)
        
        if not all_articles:
            print("❌ No articles found")
            return
        
        # Test with just 3 articles
        test_articles = all_articles[:3]
        print(f"\n🧪 Testing with {len(test_articles)} articles...")
        
        processed_articles = agent.process_multiple_articles(test_articles, preview=True)
        
        if processed_articles:
            print(f"\n✅ Test successful! Processed {len(processed_articles)} articles")
            print("💡 You can now run the full memory-efficient scraper")
            
            # Generate test outputs
            pdf_path = agent.generate_comprehensive_pdf_report(processed_articles, preview=True)
            website_path = agent.generate_website(processed_articles, pdf_path, preview=True)
            
            print(f"📄 Test PDF: {pdf_path}")
            print(f"🌐 Test Website: {website_path}")
        else:
            print("❌ Test failed - no articles processed")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_test_scraping()
    else:
        run_memory_efficient_scraping()
