import requests
from bs4 import BeautifulSoup
import time
import random
import json
import logging
from requests.exceptions import RequestException
import backoff  # You may need to install this: pip install backoff

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AmazonScraper:
    def __init__(self):
        # Expanded list of rotating user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        ]
        
        # Rotate between different bestseller categories
        self.bestseller_urls = [
            'https://www.amazon.com/Best-Sellers/zgbs',
            'https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics',
            'https://www.amazon.com/Best-Sellers-Home-Kitchen/zgbs/home-garden',
            'https://www.amazon.com/Best-Sellers-Books/zgbs/books',
            'https://www.amazon.com/Best-Sellers-Toys-Games/zgbs/toys-and-games'
        ]
        
        # Optional - List of proxies if you have them
        self.proxies = [
            # Add your proxies here in the format 'http://ip:port'
            # 'http://123.456.789.012:8080',
            # 'http://234.567.890.123:8080'
        ]
        
        self.session = requests.Session()
        self.max_retries = 5
        self.session_requests = 0
        self.session_limit = 25  # Reset session after this many requests
    
    def get_random_bestseller_url(self):
        return random.choice(self.bestseller_urls)
    
    def get_headers(self):
        """Get random user agent headers"""
        user_agent = random.choice(self.user_agents)
        return {
            'User-Agent': user_agent,
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.google.com/'
        }
    
    def get_proxy(self):
        """Get random proxy if available"""
        if self.proxies:
            return {'http': random.choice(self.proxies), 'https': random.choice(self.proxies)}
        return None
    
    @backoff.on_exception(backoff.expo, RequestException, max_tries=5)
    def make_request(self, url):
        """Make request with exponential backoff retry logic"""
        # Reset session periodically to avoid detection patterns
        if self.session_requests >= self.session_limit:
            logging.info("Creating new session after reaching request limit")
            self.session = requests.Session()
            self.session_requests = 0
            time.sleep(random.uniform(10, 20))  # Longer pause between session resets
        
        # Add jitter to avoid predictable request patterns
        delay = random.uniform(3, 10)
        logging.info(f"Waiting {delay:.2f} seconds before making request")
        time.sleep(delay)
        
        headers = self.get_headers()
        proxies = self.get_proxy()
        
        self.session_requests += 1
        
        try:
            response = self.session.get(
                url, 
                headers=headers, 
                proxies=proxies,
                timeout=(10, 30)  # Connect timeout, Read timeout
            )
            
            # Check for rate limiting
            if response.status_code == 429:
                logging.warning("Rate limited! Backing off...")
                retry_after = int(response.headers.get('Retry-After', 60))
                time.sleep(retry_after + random.uniform(5, 15))
                raise RequestException("Rate limited")
                
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Request error: {e}")
            raise
        
    def scrape_bestsellers(self, category_url=None):
        """Scrape Amazon bestsellers and return top 5 products"""
        try:
            url = category_url if category_url else self.get_random_bestseller_url()
            logging.info(f"Scraping bestsellers from: {url}")
            
            response = self.make_request(url)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all product items
            product_items = soup.select('div.p13n-sc-uncoverable-faceout')
            
            products = []
            for item in product_items[:5]:  # Get top 5 products
                try:
                    # Extract product details
                    title_elem = item.select_one('div._cDEzb_p13n-sc-css-line-clamp-1_1Fn1y')
                    price_elem = item.select_one('span._cDEzb_p13n-sc-price_3mJ9Z')
                    image_elem = item.select_one('img')
                    link_elem = item.select_one('a.a-link-normal')
                    
                    title = title_elem.text.strip() if title_elem else "No title available"
                    price = price_elem.text.strip() if price_elem else "Price not available"
                    image_url = image_elem['src'] if image_elem and 'src' in image_elem.attrs else None
                    product_url = "https://www.amazon.com" + link_elem['href'] if link_elem and 'href' in link_elem.attrs else None
                    
                    category = url.split('/zgbs/')[-1].replace('-', ' ').title() if '/zgbs/' in url else "Best Sellers"
                    
                    products.append({
                        'title': title,
                        'price': price,
                        'image_url': image_url,
                        'product_url': product_url,
                        'category': category
                    })
                    
                except Exception as e:
                    logging.error(f"Error extracting product info: {e}")
                    continue
            
            # If we didn't find products with the expected selectors, try alternative selectors
            if not products:
                alt_product_items = soup.select('div.zg-grid-general-faceout')
                
                for item in alt_product_items[:5]:  # Get top 5 products
                    try:
                        title_elem = item.select_one('div._p13n-zg-list-grid-desktop_truncationStyles_p13n-sc-css-line-clamp-1__1Fn1y')
                        price_elem = item.select_one('span.p13n-sc-price')
                        image_elem = item.select_one('img.a-dynamic-image')
                        link_elem = item.select_one('a.a-link-normal')
                        
                        title = title_elem.text.strip() if title_elem else "No title available"
                        price = price_elem.text.strip() if price_elem else "Price not available"
                        image_url = image_elem['src'] if image_elem and 'src' in image_elem.attrs else None
                        product_url = "https://www.amazon.com" + link_elem['href'] if link_elem and 'href' in link_elem.attrs else None
                        
                        category = url.split('/zgbs/')[-1].replace('-', ' ').title() if '/zgbs/' in url else "Best Sellers"
                        
                        products.append({
                            'title': title,
                            'price': price,
                            'image_url': image_url,
                            'product_url': product_url,
                            'category': category
                        })
                        
                    except Exception as e:
                        logging.error(f"Error extracting product info with alternative selectors: {e}")
                        continue
            
            logging.info(f"Successfully scraped {len(products)} bestseller products")
            return products
            
        except Exception as e:
            logging.error(f"Error scraping Amazon bestsellers: {e}")
            return []

    def run_scraper(self, num_categories=2):
        """Run the scraper for multiple categories with proper delays between requests"""
        all_products = []
        categories_scraped = 0
        
        # Choose random categories to scrape
        random_categories = random.sample(self.bestseller_urls, min(num_categories, len(self.bestseller_urls)))
        
        for category_url in random_categories:
            products = self.scrape_bestsellers(category_url)
            all_products.extend(products)
            categories_scraped += 1
            
            # Add a longer delay between categories to be extra cautious
            if categories_scraped < len(random_categories):
                delay = random.uniform(20, 45)
                logging.info(f"Completed category {categories_scraped}. Waiting {delay:.2f} seconds before next category...")
                time.sleep(delay)
        
        return all_products


if __name__ == "__main__":
    scraper = AmazonScraper()
    products = scraper.run_scraper(num_categories=2)  # Scrape 2 random categories
    
    if products:
        print(json.dumps(products, indent=2))
        # Save to file
        with open('amazon_bestsellers.json', 'w') as f:
            json.dump(products, f, indent=2)
    else:
        print("No products were found.")
