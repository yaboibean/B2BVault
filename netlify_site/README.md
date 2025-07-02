# B2B Vault Analysis Dashboard - Netlify Deployment

## 🌐 Live Features
- **Main Dashboard**: [index.html](./index.html) - View analyzed articles
- **Scraper Tool**: [scraper.html](./scraper.html) - Generate scraping commands
- **PDF Report**: Download comprehensive analysis report

## 🚀 Quick Deploy to Netlify
1. **Upload Files**: Drag the entire `netlify_site` folder to Netlify
2. **Configure**: Set publish directory to root (`.`)
3. **Deploy**: Your site will be live immediately!

## 🔧 How to Update Content

### Method 1: Use Static Scraper (Recommended)
1. Visit `/scraper.html` on your deployed site
2. Select categories and generate command
3. Run command locally: `python3 B2Bscraper.py --tags="Sales,Marketing" --generate-netlify`
4. Re-upload the generated files

### Method 2: Local Development
```bash
# Clone the repository
git clone [your-repo-url]
cd B2BVaultScraper

# Install dependencies
pip install playwright beautifulsoup4 flask requests tenacity weasyprint

# Run scraper
python3 B2Bscraper.py --tags="Sales,Marketing,AI"

# Prepare for Netlify
python3 prepare_netlify_deployment.py

# Upload netlify_site folder to Netlify
```

## 📁 File Structure
```
netlify_site/
├── index.html              # Main dashboard
├── scraper.html            # Static tag selector
├── *.pdf                   # Analysis reports
├── netlify.toml           # Netlify configuration
├── _redirects             # URL redirects
└── README.md              # This file
```

## 🎯 Supported Categories
All, Content Marketing, Demand Generation, ABM & GTM, Paid Marketing, Marketing Ops, Event Marketing, AI, Product Marketing, Sales, General, Affiliate & Partnerships, Copy & Positioning

## 📊 Features
- ✅ **Responsive Design**: Works on desktop and mobile
- ✅ **Search Functionality**: Find articles quickly
- ✅ **PDF Downloads**: Complete analysis reports
- ✅ **SEO Optimized**: Meta tags and proper structure
- ✅ **Fast Loading**: Optimized static files

## 🔗 Useful Links
- Dashboard: `/` or `/dashboard`
- Scraper: `/scraper`
- PDF Report: `/*.pdf`

---
Generated on: 2025-07-01 15:49:32
Deployment ready! 🚀
