import os
import requests
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import urljoin, urlparse
import json

class AmazonPinterestBot:
    def __init__(self):
        self.pinterest_token = os.getenv('PINTEREST_ACCESS_TOKEN')
        self.affiliate_tag = os.getenv('AMAZON_AFFILIATE_TAG')
        self.board_id = os.getenv('PINTEREST_BOARD_ID')
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def get_bestsellers(self, category_url):
        response = requests.get(category_url, headers=self.headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        products = []
        items = soup.find_all('div', {'data-component-type': 'bestseller-productDetails'})
        
        for item in items[:5]:  # Top 5 products
            try:
                title_elem = item.find('h3') or item.find('span', {'class': 'a-truncate-cut'})
                title = title_elem.get_text(strip=True) if title_elem else None
                
                link_elem = item.find('a', href=True)
                product_url = urljoin('https://amazon.com', link_elem['href']) if link_elem else None
                
                img_elem = item.find('img')
                image_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else None
                
                if title and product_url and image_url:
                    affiliate_url = f"{product_url}&tag={self.affiliate_tag}"
                    products.append({
                        'title': title[:100],
                        'url': affiliate_url,
                        'image': image_url.replace('_AC_UL300_SR300,200_', '_AC_UL600_SR600,400_'),
                        'description': f"✨ Amazon Bestseller: {title[:80]}... 🛒 Check price & reviews!"
                    })
            except:
                continue
                
        return products
    
    def create_pinterest_pin(self, product):
        url = "https://api.pinterest.com/v5/pins"
        headers = {
            'Authorization': f'Bearer {self.pinterest_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'link': product['url'],
            'title': product['title'],
            'description': product['description'],
            'board_id': self.board_id,
            'media_source': {
                'source_type': 'image_url',
                'url': product['image']
            }
        }
        
        response = requests.post(url, headers=headers, json=data)
        return response.status_code == 201
    
    def run(self):
        categories = [
            'https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics',
            'https://www.amazon.com/Best-Sellers-Home-Kitchen/zgbs/home-garden',
            'https://www.amazon.com/Best-Sellers-Sports-Outdoors/zgbs/sporting-goods',
            'https://www.amazon.com/Best-Sellers-Health-Personal-Care/zgbs/hpc',
        ]
        
        total_pins = 0
        for category in categories:
            products = self.get_bestsellers(category)
            
            for product in products:
                if self.create_pinterest_pin(product):
                    total_pins += 1
                    print(f"✅ Pinned: {product['title'][:50]}...")
                else:
                    print(f"❌ Failed: {product['title'][:50]}...")
                
                time.sleep(random.uniform(2, 5))
            
            time.sleep(random.uniform(10, 20))
        
        print(f"🎯 Total pins created: {total_pins}")

if __name__ == "__main__":
    bot = AmazonPinterestBot()
    bot.run()
