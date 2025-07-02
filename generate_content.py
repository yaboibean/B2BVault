#!/usr/bin/env python3
"""
Dedicated script to generate all B2B Vault content for static website
"""
import os
import sys
from B2Bscraper import B2BVaultAgent

def main():
    print("🚀 B2B Vault Content Generator")
    print("=" * 50)
    print("This script will:")
    print("1. Scrape ALL articles from B2B Vault")
    print("2. Process them with AI analysis")
    print("3. Generate a comprehensive website")
    print("4. Create PDF reports")
    print("5. Prepare everything for static hosting")
    print("=" * 50)
    
    # Ask for confirmation
    response = input("\nStart comprehensive scraping? This may take 30-60 minutes. (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ Scraping cancelled.")
        return
    
    print("\n🌐 Starting comprehensive B2B Vault scraping...")
    
    # Initialize scraper
    agent = B2BVaultAgent(max_workers=5)
    
    # Step 1: Collect ALL articles
    print(f"\n📑 Step 1: Collecting articles from ALL categories...")
    all_articles = agent.scrape_all_articles(preview=True)
    
    if not all_articles:
        print("❌ No articles found")
        return
    
    print(f"\n📊 Collected {len(all_articles)} total articles")
    
    # Step 2: Process with AI
    print(f"\n🤖 Step 2: Processing articles with AI analysis...")
    processed_articles = agent.process_multiple_articles_parallel(all_articles, preview=True)
    
    if not processed_articles:
        print("❌ No articles were successfully processed")
        return
    
    print(f"\n✅ Successfully processed {len(processed_articles)} articles")
    
    # Step 3: Generate outputs
    print(f"\n📄 Step 3: Generating PDF report...")
    pdf_path = agent.generate_comprehensive_pdf_report(processed_articles, preview=True)
    
    print(f"\n🌐 Step 4: Generating website...")
    website_path = agent.generate_advanced_website(processed_articles, pdf_path, preview=True)
    
    print(f"\n🎉 CONTENT GENERATION COMPLETE!")
    print(f"📊 Statistics:")
    print(f"   • Total articles scraped: {len(all_articles)}")
    print(f"   • Articles processed: {len(processed_articles)}")
    print(f"   • Categories: {len(set(a['tab'] for a in all_articles))}")
    print(f"   • Publishers: {len(set(a['publisher'] for a in all_articles))}")
    print(f"   • PDF report: {pdf_path}")
    print(f"   • Website: {website_path}")
    
    print(f"\n📋 Next Steps:")
    print(f"1. Run: python3 prepare_netlify_deployment.py")
    print(f"2. Upload the netlify_site folder to your hosting platform")
    print(f"3. Your dashboard will be live with all the analyzed articles!")

if __name__ == "__main__":
    main()
