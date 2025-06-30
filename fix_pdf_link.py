#!/usr/bin/env python3
"""
Script to fix the PDF link in the netlify site by finding and copying the actual PDF file
"""
import os
import shutil
import glob

def find_and_copy_pdf():
    """Find the generated PDF and copy it to the netlify_site directory"""
    
    # Look for PDF files in the scraped_data directory
    scraped_data_dir = "scraped_data"
    netlify_site_dir = "netlify_site"
    
    if not os.path.exists(scraped_data_dir):
        print("❌ scraped_data directory not found!")
        return False
    
    if not os.path.exists(netlify_site_dir):
        print("❌ netlify_site directory not found!")
        return False
    
    # Find all PDF files in scraped_data
    pdf_files = glob.glob(os.path.join(scraped_data_dir, "*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in scraped_data directory!")
        print("   Run the scraper first to generate a PDF report.")
        return False
    
    # Find the comprehensive report (should have the most recent timestamp)
    comprehensive_pdfs = [f for f in pdf_files if "comprehensive_report" in f]
    
    if comprehensive_pdfs:
        # Use the most recent comprehensive report
        latest_pdf = max(comprehensive_pdfs, key=os.path.getmtime)
    else:
        # Use the most recent PDF file
        latest_pdf = max(pdf_files, key=os.path.getmtime)
    
    print(f"📄 Found PDF: {latest_pdf}")
    
    # Copy the PDF to netlify_site with the expected name
    expected_name = "b2b_vault_comprehensive_report_20250630_161238.pdf"
    dest_path = os.path.join(netlify_site_dir, expected_name)
    
    try:
        shutil.copy2(latest_pdf, dest_path)
        print(f"✅ PDF copied to: {dest_path}")
        print(f"🌐 The website should now be able to access the PDF file")
        return True
    except Exception as e:
        print(f"❌ Error copying PDF: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing PDF link for netlify site...")
    success = find_and_copy_pdf()
    
    if success:
        print("\n✅ PDF link fixed!")
        print("💡 You can now serve the website and the PDF download should work.")
    else:
        print("\n❌ Failed to fix PDF link.")
        print("💡 Make sure you have run the scraper to generate a PDF first.")
