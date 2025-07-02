#!/usr/bin/env python3
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
    print("\n📊 Step 1: Running B2B Vault scraper...")
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
    print("\n🚀 Step 2: Deploying to Netlify...")
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
        print("\n✅ Complete pipeline successful!")
    else:
        print("\n❌ Pipeline failed - check errors above")
        sys.exit(1)
