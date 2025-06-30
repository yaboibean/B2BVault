"""
Configuration settings for the B2B Vault Scraper
"""

# Scraping settings
DEFAULT_DELAY = 1.0  # Seconds between requests
REQUEST_TIMEOUT = 10  # Seconds
MAX_RETRIES = 3

# Output settings
OUTPUT_DIR = "scraped_data"
CSV_FILENAME = "scraped_companies.csv"
JSON_FILENAME = "scraped_companies.json"

# User agent for requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Common selectors for company information
COMPANY_NAME_SELECTORS = [
    'h1',
    '.company-name',
    '#company-name',
    'title',
    '.site-title',
    '.logo',
    '.brand-name'
]

DESCRIPTION_SELECTORS = [
    'meta[name="description"]',
    '.description',
    '.about',
    '.company-description'
]

# Social media domains to look for
SOCIAL_DOMAINS = [
    'facebook.com',
    'twitter.com',
    'linkedin.com',
    'instagram.com',
    'youtube.com',
    'github.com'
]

# Regex patterns
EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
PHONE_PATTERN = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
