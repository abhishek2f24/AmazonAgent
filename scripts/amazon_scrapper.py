import requests
from bs4 import BeautifulSoup
import time
import random
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AmazonScraper:
    def __init__(self):
        self.user_agents = [
            # Rotate through different common browsers
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36'
        ]
        self.bestseller_urls = [
            'https://www.amazon.com/Best-Sellers/zgbs',
            'https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics',
            'https://www.amazon.com/Best-Sellers-Home-Kitchen/zgbs/home-garden',
            'https://www.amazon.com/Best-Sellers-Books/zgbs/books',
            'https://www.amazon.com/Best-Sellers-Toys-Games/zgbs/toys-and-games'
        ]
    
    def get_random_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept-Language': 'en-US,en;q=0.9',
        }

    def get_random_bestseller_url(self):
        return random.choice(self.bestseller_urls)
    
    def get_with_retries(self, url, retries=5, backoff_factor=2):
        """Handle retries and delay for 429 errors"""
        for attempt in range(retries):
            try:
                headers = self.get_random_headers()
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 429:
                    logging.warning(f"Rate limited (429). Retrying in {backoff_factor ** attempt}s...")
                    time.sleep(backoff_factor ** attempt)
                    continue
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed (attempt {attempt + 1}): {e}")
                time.sleep(backoff_factor ** attempt)
        raise Exception("Exceeded retry limit")

    def scrape_bestsellers(self, category_url=None):
        try:
            url = category_url or self.get_random_bestseller_url()
            logging.info(f"Scraping bestsellers from: {url}")

            response = self.get_with_retries(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            product_items = soup.select('div.p13n-sc-uncoverable-faceout')
            products = []

            for item in product_items[:5]:
                try:
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

            logging.info(f"Successfully scraped {len(products)} products")
            return products

        except Exception as e:
            logging.error(f"Failed to scrape: {e}")
            return []
