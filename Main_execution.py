#!/usr/bin/env python3
"""
Amazon Bestseller to Pinterest Pin Creator
A tool for scraping Amazon bestsellers and creating Pinterest pins for affiliate marketing.
"""

import os
import json
import time
import random
import requests
from datetime import datetime
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional
import logging
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from py3pin.Pinterest import Pinterest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('amazon_pinterest_tool.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Product:
    """Data class for Amazon product information"""
    title: str
    description: str
    price: str
    image_url: str
    amazon_url: str
    asin: str
    rating: Optional[str] = None
    review_count: Optional[str] = None

class AmazonScraper:
    """Scraper for Amazon bestseller products"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # For GitHub Actions
        if os.getenv('GITHUB_ACTIONS'):
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def get_bestsellers(self, category_url: str, max_products: int = 20) -> List[Product]:
        """
        Scrape Amazon bestsellers from a specific category
        
        Args:
            category_url: Amazon bestsellers category URL
            max_products: Maximum number of products to scrape
            
        Returns:
            List of Product objects
        """
        products = []
        
        try:
            logger.info(f"Scraping Amazon bestsellers from: {category_url}")
            self.driver.get(category_url)
            
            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="bestseller-item"]'))
            )
            
            # Find all product items
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="bestseller-item"]')
            
            for i, element in enumerate(product_elements[:max_products]):
                try:
                    product = self.extract_product_info(element)
                    if product:
                        products.append(product)
                        logger.info(f"Scraped product {i+1}: {product.title[:50]}...")
                    
                    # Random delay to avoid being blocked
                    time.sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    logger.warning(f"Failed to extract product {i+1}: {e}")
                    continue
            
            logger.info(f"Successfully scraped {len(products)} products")
            return products
            
        except TimeoutException:
            logger.error("Page took too long to load")
            return []
        except Exception as e:
            logger.error(f"Error scraping bestsellers: {e}")
            return []
    
    def extract_product_info(self, element) -> Optional[Product]:
        """Extract product information from a product element"""
        try:
            # Extract title
            title_elem = element.find_element(By.CSS_SELECTOR, 'h2 a, .p13n-sc-truncate')
            title = title_elem.text.strip()
            
            # Extract product URL and ASIN
            link_elem = element.find_element(By.CSS_SELECTOR, 'h2 a')
            product_url = link_elem.get_attribute('href')
            asin = self.extract_asin_from_url(product_url)
            
            # Extract image URL
            img_elem = element.find_element(By.CSS_SELECTOR, 'img')
            image_url = img_elem.get_attribute('src')
            
            # Extract price
            try:
                price_elem = element.find_element(By.CSS_SELECTOR, '.p13n-sc-price, .a-price .a-offscreen')
                price = price_elem.text.strip()
            except NoSuchElementException:
                price = "Price not available"
            
            # Extract rating (optional)
            try:
                rating_elem = element.find_element(By.CSS_SELECTOR, '.a-icon-alt')
                rating = rating_elem.get_attribute('textContent')
            except NoSuchElementException:
                rating = None
            
            # Generate description from title (you can enhance this)
            description = self.generate_description(title)
            
            # Convert to affiliate URL if needed
            affiliate_url = self.add_affiliate_tag(product_url)
            
            return Product(
                title=title,
                description=description,
                price=price,
                image_url=image_url,
                amazon_url=affiliate_url,
                asin=asin,
                rating=rating
            )
            
        except Exception as e:
            logger.warning(f"Failed to extract product info: {e}")
            return None
    
    def extract_asin_from_url(self, url: str) -> str:
        """Extract ASIN from Amazon product URL"""
        try:
            if '/dp/' in url:
                return url.split('/dp/')[1].split('/')[0]
            elif '/gp/product/' in url:
                return url.split('/gp/product/')[1].split('/')[0]
            else:
                return ""
        except:
            return ""
    
    def add_affiliate_tag(self, url: str) -> str:
        """Add affiliate tag to Amazon URL"""
        affiliate_tag = os.getenv('AMAZON_AFFILIATE_TAG', 'your-affiliate-tag')
        
        if '?' in url:
            return f"{url}&tag={affiliate_tag}"
        else:
            return f"{url}?tag={affiliate_tag}"
    
    def generate_description(self, title: str) -> str:
        """Generate a Pinterest-friendly description from product title"""
        templates = [
            f"🛍️ Amazing deal on {title}! Perfect for your home and lifestyle. Check it out! #AmazonFinds #Shopping #Deal",
            f"✨ Trending now: {title}! Don't miss out on this popular item. #BestSeller #Amazon #MustHave",
            f"🎯 Found the perfect {title}! Great quality and amazing reviews. #ProductReview #Shopping #Recommended",
            f"💡 Looking for {title}? This bestseller has amazing reviews! #AmazonBestseller #Shopping #TopRated"
        ]
        
        return random.choice(templates)
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")

class PinterestManager:
    """Manager for Pinterest operations"""
    
    def __init__(self):
        self.pinterest = None
        self.setup_pinterest()
    
    def setup_pinterest(self):
        """Setup Pinterest API client"""
        try:
            email = os.getenv('PINTEREST_EMAIL')
            password = os.getenv('PINTEREST_PASSWORD')
            
            if not email or not password:
                raise ValueError("Pinterest credentials not found in environment variables")
            
            self.pinterest = Pinterest(email=email, password=password)
            logger.info("Pinterest client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinterest client: {e}")
            raise
    
    def create_pin(self, product: Product, board_name: str) -> bool:
        """
        Create a Pinterest pin from product information
        
        Args:
            product: Product object with pin information
            board_name: Pinterest board name to pin to
            
        Returns:
            True if pin created successfully, False otherwise
        """
        try:
            # Download and upload image
            image_path = self.download_image(product.image_url, product.asin)
            
            if not image_path:
                logger.warning(f"Failed to download image for {product.title}")
                return False
            
            # Create pin
            pin_result = self.pinterest.pin(
                board_name=board_name,
                image_path=image_path,
                description=product.description,
                link=product.amazon_url,
                title=product.title[:100]  # Pinterest title limit
            )
            
            # Clean up downloaded image
            if os.path.exists(image_path):
                os.remove(image_path)
            
            if pin_result:
                logger.info(f"Successfully created pin for: {product.title[:50]}...")
                return True
            else:
                logger.warning(f"Failed to create pin for: {product.title[:50]}...")
                return False
                
        except Exception as e:
            logger.error(f"Error creating pin for {product.title}: {e}")
            return False
    
    def download_image(self, image_url: str, filename: str) -> Optional[str]:
        """Download product image for Pinterest upload"""
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Create images directory if it doesn't exist
            os.makedirs('temp_images', exist_ok=True)
            
            image_path = f"temp_images/{filename}.jpg"
            
            with open(image_path, 'wb') as f:
                f.write(response.content)
            
            return image_path
            
        except Exception as e:
            logger.error(f"Failed to download image {image_url}: {e}")
            return None
    
    def get_boards(self) -> List[str]:
        """Get list of user's Pinterest boards"""
        try:
            boards = self.pinterest.boards()
            return [board['name'] for board in boards]
        except Exception as e:
            logger.error(f"Failed to get boards: {e}")
            return []

class AmazonPinterestTool:
    """Main tool class that orchestrates the scraping and pinning process"""
    
    def __init__(self):
        self.scraper = AmazonScraper(headless=True)
        self.pinterest = PinterestManager()
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from environment variables or config file"""
        config = {
            'amazon_categories': os.getenv('AMAZON_CATEGORIES', '').split(','),
            'pinterest_board': os.getenv('PINTEREST_BOARD', 'Amazon Finds'),
            'max_products_per_category': int(os.getenv('MAX_PRODUCTS_PER_CATEGORY', '10')),
            'delay_between_pins': int(os.getenv('DELAY_BETWEEN_PINS', '60')),  # seconds
        }
        
        # Default categories if none provided
        if not config['amazon_categories'] or config['amazon_categories'] == ['']:
            config['amazon_categories'] = [
                'https://www.amazon.com/Best-Sellers-Home-Kitchen/zgbs/home-garden',
                'https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics',
                'https://www.amazon.com/Best-Sellers-Books/zgbs/books'
            ]
        
        return config
    
    def run(self):
        """Main execution method"""
        logger.info("Starting Amazon to Pinterest tool")
        
        total_pins_created = 0
        
        try:
            for category_url in self.config['amazon_categories']:
                logger.info(f"Processing category: {category_url}")
                
                # Scrape products from Amazon
                products = self.scraper.get_bestsellers(
                    category_url, 
                    self.config['max_products_per_category']
                )
                
                if not products:
                    logger.warning(f"No products found for category: {category_url}")
                    continue
                
                # Create Pinterest pins
                for product in products:
                    success = self.pinterest.create_pin(
                        product, 
                        self.config['pinterest_board']
                    )
                    
                    if success:
                        total_pins_created += 1
                    
                    # Delay between pins to avoid rate limiting
                    time.sleep(self.config['delay_between_pins'])
                
                # Delay between categories
                time.sleep(random.uniform(60, 120))
            
            logger.info(f"Tool completed successfully! Created {total_pins_created} pins")
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            raise
        
        finally:
            self.scraper.close()
    
    def save_products_json(self, products: List[Product], filename: str = None):
        """Save scraped products to JSON file for debugging"""
        if not filename:
            filename = f"scraped_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        products_data = [
            {
                'title': p.title,
                'description': p.description,
                'price': p.price,
                'image_url': p.image_url,
                'amazon_url': p.amazon_url,
                'asin': p.asin,
                'rating': p.rating
            }
            for p in products
        ]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(products_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(products)} products to {filename}")

def main():
    """Main function for command line execution"""
    try:
        tool = AmazonPinterestTool()
        tool.run()
    except KeyboardInterrupt:
        logger.info("Tool stopped by user")
    except Exception as e:
        logger.error(f"Tool failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()
