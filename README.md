# B2B Vault Scraper

A Python web scraper designed to extract company and contact information from B2B websites.

## Features

- Extract company names, descriptions, contact info
- Find email addresses and phone numbers
- Collect social media links
- Export data to CSV and JSON formats
- Respectful scraping with configurable delays
- Comprehensive logging

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from B2Bscraper import B2BVaultScraper

# Initialize scraper
scraper = B2BVaultScraper(delay=1.0)

# Scrape a single URL
data = scraper.scrape_url("https://example.com")

# Scrape multiple URLs
urls = ["https://company1.com", "https://company2.com"]
results = scraper.scrape_urls(urls)

# Save results
scraper.save_to_csv(results)
scraper.save_to_json(results)
```

### Advanced Usage

```python
# Custom configuration
scraper = B2BVaultScraper(
    delay=2.0,  # 2 second delay between requests
    output_dir="my_scraped_data"
)

# Process results
for company in results:
    print(f"Company: {company['company_name']}")
    print(f"Email: {company['email']}")
    print(f"Phone: {company['phone']}")
    print("---")
```

## Configuration

Edit `config.py` to customize:
- Request delays and timeouts
- CSS selectors for data extraction
- Output file names and formats
- Social media domains to track

## Output

The scraper generates:
- `scraped_companies.csv` - Tabular data
- `scraped_companies.json` - Structured data
- `scraper.log` - Execution logs
- `last_fetched_page.html` - Last fetched page for debugging

## Legal and Ethical Considerations

- Always respect robots.txt files
- Use appropriate delays between requests
- Don't overload target servers
- Comply with website terms of service
- Follow applicable data protection laws

## License

This project is for educational and research purposes.
