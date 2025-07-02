#!/usr/bin/env python3
"""
Enhanced script to prepare files for Netlify deployment and automatically sync
"""
import os
import shutil
import glob
import time
import subprocess

netlify_site_dir = "netlify_site"
scraped_data_dir = "scraped_data"

def auto_deploy_to_netlify():
    """Automatically deploy to Netlify if Netlify CLI is available"""
    try:
        # Check if Netlify CLI is installed
        result = subprocess.run(['netlify', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("🚀 Netlify CLI detected! Attempting auto-deployment...")
            
            # Change to netlify_site directory
            original_dir = os.getcwd()
            os.chdir(netlify_site_dir)
            
            try:
                # Deploy to Netlify
                deploy_result = subprocess.run(['netlify', 'deploy', '--prod', '--dir', '.'], 
                                             capture_output=True, text=True, timeout=60)
                
                if deploy_result.returncode == 0:
                    print("✅ Successfully deployed to Netlify!")
                    print("🌐 Your dashboard should be updated within a few minutes")
                    return True
                else:
                    print(f"❌ Netlify deployment failed: {deploy_result.stderr}")
                    return False
                    
            finally:
                os.chdir(original_dir)
                
        else:
            print("⚠️  Netlify CLI not found")
            return False
            
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️  Netlify CLI not available")
        return False

def prepare_netlify_deployment():
    """Prepare all files for Netlify deployment with auto-sync"""
    
    print("🚀 Preparing Netlify deployment with latest scraped data...")
    
    # Create netlify_site directory
    os.makedirs(netlify_site_dir, exist_ok=True)
    
    # 1. Check for and copy the main dashboard
    website_dir = os.path.join(scraped_data_dir, "website")
    dashboard_exists = False
    
    if os.path.exists(os.path.join(website_dir, "index.html")):
        print("✅ Copying latest dashboard...")
        shutil.copy2(os.path.join(website_dir, "index.html"), 
                    os.path.join(netlify_site_dir, "index.html"))
        dashboard_exists = True
        
        # Copy any additional files from the website
        for file_pattern in ["*.css", "*.js", "*.png", "*.jpg", "*.ico"]:
            for file_path in glob.glob(os.path.join(website_dir, file_pattern)):
                shutil.copy2(file_path, netlify_site_dir)
                print(f"✅ Copied: {os.path.basename(file_path)}")
                
    else:
        print("⚠️  No analysis dashboard found")
        print("   💡 Run 'python3 B2Bscraper.py --preview' first")
    
    # 2. Copy latest PDF files
    if os.path.exists(scraped_data_dir):
        pdf_files = glob.glob(os.path.join(scraped_data_dir, "*comprehensive_report*.pdf"))
        if pdf_files:
            latest_pdf = max(pdf_files, key=os.path.getmtime)
            dest_pdf_path = os.path.join(netlify_site_dir, os.path.basename(latest_pdf))
            
            try:
                shutil.copy2(latest_pdf, dest_pdf_path)
                print(f"✅ Copied latest PDF: {os.path.basename(latest_pdf)}")
            except Exception as e:
                print(f"❌ Error copying PDF: {e}")
    
    # 3. Update file timestamps for Netlify cache busting
    for root, dirs, files in os.walk(netlify_site_dir):
        for file in files:
            file_path = os.path.join(root, file)
            # Touch the file to update timestamp
            os.utime(file_path, None)
    
    print(f"\n📊 NETLIFY DEPLOYMENT STATUS:")
    if dashboard_exists:
        print("   ✅ Latest dashboard ready for deployment!")
        print("   📊 Main page: Analysis dashboard (index.html)")
        print("   📄 Latest PDF report included")
    else:
        print("   📋 Placeholder dashboard (no fresh content)")
    
    # 4. Attempt automatic deployment
    print(f"\n🚀 ATTEMPTING AUTO-DEPLOYMENT...")
    auto_deployed = auto_deploy_to_netlify()
    
    if auto_deployed:
        print("🎉 SUCCESS! Your Netlify site has been updated automatically!")
    else:
        print("📋 MANUAL DEPLOYMENT REQUIRED:")
        print("   1. Install Netlify CLI: npm install -g netlify-cli")
        print("   2. Run: netlify login")
        print("   3. Run: netlify init (first time only)")
        print("   4. Run this script again for auto-deployment")
        print("   OR")
        print("   📁 Manually upload the 'netlify_site' folder to Netlify dashboard")
    
    return dashboard_exists

def create_auto_update_script():
    """Create a script that automatically updates Netlify after scraping"""
    script_content = '''#!/usr/bin/env python3
"""
Auto-update script: Run scraper and deploy to Netlify in one command
"""
import subprocess
import sys
import os

def run_scraper_and_deploy():
    """Run the scraper and automatically deploy to Netlify"""
    print("🚀 Starting B2B Vault scraper with auto-deployment...")
    
    # Step 1: Run the scraper
    print("\\n📊 Step 1: Running B2B Vault scraper...")
    try:
        scraper_result = subprocess.run([
            sys.executable, 'B2Bscraper.py', '--preview', '--limit', '50'
        ], timeout=1800)  # 30 minute timeout
        
        if scraper_result.returncode != 0:
            print("❌ Scraper failed!")
            return False
            
        print("✅ Scraper completed successfully!")
        
    except subprocess.TimeoutExpired:
        print("❌ Scraper timed out after 30 minutes")
        return False
    except Exception as e:
        print(f"❌ Scraper error: {e}")
        return False
    
    # Step 2: Prepare and deploy to Netlify
    print("\\n🚀 Step 2: Deploying to Netlify...")
    try:
        deploy_result = subprocess.run([
            sys.executable, 'prepare_netlify_deployment.py'
        ], timeout=300)  # 5 minute timeout
        
        if deploy_result.returncode == 0:
            print("🎉 SUCCESS! Your Netlify dashboard has been updated!")
            print("🌐 Check your live site in a few minutes")
            return True
        else:
            print("❌ Deployment failed!")
            return False
            
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        return False

if __name__ == "__main__":
    success = run_scraper_and_deploy()
    if success:
        print("\\n✅ Complete pipeline successful!")
    else:
        print("\\n❌ Pipeline failed - check errors above")
        sys.exit(1)
'''
    
    script_path = "auto_update_netlify.py"
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    # Make executable
    try:
        os.chmod(script_path, 0o755)
    except:
        pass
    
    print(f"✅ Created auto-update script: {script_path}")
    print("💡 Usage: python3 auto_update_netlify.py")

if __name__ == "__main__":
    prepare_netlify_deployment()
    create_auto_update_script()
        
