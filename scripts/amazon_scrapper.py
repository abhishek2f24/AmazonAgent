import requests
from bs4 import BeautifulSoup
import time
import random
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AmazonScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        # Rotate between different bestseller categories
        self.bestseller_urls = [
            'https://www.amazon.com/Best-Sellers/zgbs',
            'https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics',
            'https://www.amazon.com/Best-Sellers-Home-Kitchen/zgbs/home-garden',
            'https://www.amazon.com/Best-Sellers-Books/zgbs/books',
            'https://www.amazon.com/Best-Sellers-Toys-Games/zgbs/toys-and-games'
        ]
    
    def get_random_bestseller_url(self):
        return random.choice(self.bestseller_urls)
        
    def scrape_bestsellers(self, category_url=None):
        """Scrape Amazon bestsellers and return top 5 products"""
        try:
            url = category_url if category_url else self.get_random_bestseller_url()
            logging.info(f"Scraping bestsellers from: {url}")
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
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