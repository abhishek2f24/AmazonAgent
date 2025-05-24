import os
import requests
from bs4 import BeautifulSoup
import time
import random
import json
from urllib.parse import urljoin

class AmazonPinterestBot:
    def __init__(self):
        self.pinterest_email = os.getenv('PINTEREST_EMAIL')
        self.pinterest_password = os.getenv('PINTEREST_PASSWORD')
        self.affiliate_tag = os.getenv('AMAZON_AFFILIATE_TAG')
        self.board_name = os.getenv('PINTEREST_BOARD_NAME', 'Amazon Deals')
        
        self.session = requests.Session()
        self.pinterest_session = requests.Session()
        
        # Rotating User Agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
    def login_pinterest(self):
        login_url = 'https://www.pinterest.com/resource/UserSessionResource/create/'
        
        # Get initial page for CSRF token
        self.pinterest_session.get('https://www.pinterest.com/login/')
        
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        
        login_data = {
            'source_url': '/login/',
            'data': json.dumps({
                'options': {
                    'username_or_email': self.pinterest_email,
                    'password': self.pinterest_password
                },
                'context': {}
            })
        }
        
        response = self.pinterest_session.post(login_url, data=login_data, headers=headers)
        return response.status_code == 200
    
    def get_board_id(self):
        boards_url = 'https://www.pinterest.com/resource/BoardsResource/get/'
        params = {
            'source_url': f'/{self.pinterest_email.split("@")[0]}/',
            'data': json.dumps({
                'options': {'username': self.pinterest_email.split('@')[0]},
                'context': {}
            })
        }

        response = self.pinterest_session.get(boards_url, params=params)
        if response.status_code == 200:
            data = response.json()
            boards = data.get('resource_response', {}).get('data', [])
            
            print(f"📋 Available boards:")
            for board in boards:
                print(f"- {board.get('name')} (ID: {board.get('id')})")
            
            for board in boards:
                if board.get('name', '').strip().lower() == self.board_name.strip().lower():
                    print(f"✅ Match found for board: {board.get('name')}")
                    return board.get('id')
            print(f"❌ Board '{self.board_name}' not found in list.")
        else:
            print(f"❌ Failed to fetch boards: {response.status_code}")
        return None

    
    def get_bestsellers(self, category_url):
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Random delay before request
        time.sleep(random.uniform(3, 8))
        
        try:
            response = self.session.get(category_url, headers=headers, timeout=15)
            if response.status_code == 429:
                print("Rate limited, waiting longer...")
                time.sleep(random.uniform(30, 60))
                return []
                
            soup = BeautifulSoup(response.content, 'html.parser')
            products = []
            
            # Multiple selectors for different Amazon layouts
            selectors = [
                'div[data-component-type="bestseller-productDetails"]',
                '.s-result-item',
                '.p13n-sc-uncoverable-faceout'
            ]
            
            items = []
            for selector in selectors:
                items = soup.select(selector)
                if items:
                    break
            
            for item in items[:3]:  # Reduced to 3 to avoid rate limits
                try:
                    # Title extraction
                    title_elem = (item.select_one('h3 a span') or 
                                item.select_one('h2 a span') or 
                                item.select_one('.s-size-mini span') or
                                item.select_one('._cDEzb_p13n-sc-css-line-clamp-1_1Fn1y'))
                    
                    title = title_elem.get_text(strip=True) if title_elem else None
                    
                    # Link extraction
                    link_elem = item.select_one('a[href*="/dp/"], a[href*="/gp/product/"]')
                    product_url = urljoin('https://amazon.com', link_elem['href']) if link_elem else None
                    
                    # Image extraction
                    img_elem = item.select_one('img')
                    image_url = None
                    if img_elem:
                        image_url = (img_elem.get('src') or 
                                   img_elem.get('data-src') or 
                                   img_elem.get('srcset', '').split(',')[0].split(' ')[0])
                    
                    if title and product_url and image_url:
                        # Clean product URL and add affiliate tag
                        clean_url = product_url.split('?')[0].split('/ref=')[0]
                        affiliate_url = f"{clean_url}?tag={self.affiliate_tag}"
                        
                        # Enhance image quality
                        if '_AC_' in image_url:
                            image_url = image_url.replace('_AC_UL300_SR300,200_', '_AC_UL800_SR800,600_')
                        
                        products.append({
                            'title': title[:100],
                            'url': affiliate_url,
                            'image': image_url,
                            'description': f"🔥 #{random.choice(['BestSeller', 'AmazonFinds', 'DealsAlert'])} {title[:70]}... 💰 Great price & reviews! #affiliate"
                        })
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error scraping {category_url}: {str(e)}")
            
        # Longer delay after scraping
        time.sleep(random.uniform(8, 15))
        return products
    
    def create_pinterest_pin(self, product, board_id):
        pin_url = 'https://www.pinterest.com/resource/PinResource/create/'
        
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        
        pin_data = {
            'source_url': '/pin-builder/',
            'data': json.dumps({
                'options': {
                    'board_id': board_id,
                    'description': product['description'],
                    'link': product['url'],
                    'image_url': product['image'],
                    'method': 'scraped'
                },
                'context': {}
            })
        }
        
        time.sleep(random.uniform(5, 10))  # Rate limiting for Pinterest
        
        try:
            response = self.pinterest_session.post(pin_url, data=pin_data, headers=headers)
            return response.status_code == 200
        except:
            return False
    
    def run(self):
        if not self.login_pinterest():
            print("❌ Pinterest login failed")
            return
            
        board_id = self.get_board_id()
        if not board_id:
            print("❌ Board not found")
            return
            
        print("✅ Pinterest authenticated")
        
        categories = [
            'https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics',
            'https://www.amazon.com/Best-Sellers-Home-Kitchen/zgbs/home-garden'
        ]
        
        total_pins = 0
        for i, category in enumerate(categories):
            print(f"🔍 Scraping category {i+1}/{len(categories)}")
            products = self.get_bestsellers(category)
            
            for product in products:
                if self.create_pinterest_pin(product, board_id):
                    total_pins += 1
                    print(f"✅ Pinned: {product['title'][:40]}...")
                else:
                    print(f"❌ Failed: {product['title'][:40]}...")
                
                # Longer delays between pins
                time.sleep(random.uniform(15, 25))
            
            # Much longer delay between categories
            if i < len(categories) - 1:
                time.sleep(random.uniform(60, 120))
        
        print(f"🎯 Total pins created: {total_pins}")

if __name__ == "__main__":
    bot = AmazonPinterestBot()
    bot.run()
