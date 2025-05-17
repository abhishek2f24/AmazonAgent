import os
import requests
import logging
import json
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PinterestPoster:
    def __init__(self, access_token=None, board_id=None):
        self.access_token = access_token or os.environ.get('PINTEREST_ACCESS_TOKEN')
        self.board_id = board_id or os.environ.get('PINTEREST_BOARD_ID')
        self.api_base_url = "https://api.pinterest.com/v5"
        
    def post_to_pinterest(self, image_path, product_data, seo_content):
        """Post image to Pinterest with SEO content"""
        try:
            logging.info(f"Posting to Pinterest: {seo_content['title']}")
            
            # Endpoint for creating pins
            url = f"{self.api_base_url}/pins"
            
            # Prepare the headers
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            # Create a link to the product on Amazon (if available)
            destination_url = product_data.get('product_url', f"https://www.amazon.com/s?k={product_data['title'].replace(' ', '+')}")
            
            # First, upload the image to get a media ID
            media_id = self.upload_image(image_path)
            if not media_id:
                logging.error("Failed to upload image to Pinterest")
                return False
                
            # Prepare the data for creating a pin
            data = {
                'title': seo_content['title'],
                'description': seo_content['description'],
                'board_id': self.board_id,
                'media_source': {
                    'media_id': media_id
                },
                'link': destination_url,
                'alt_text': product_data['title']
            }
            
            # Make the API request
            response = requests.post(url, headers=headers, json=data)
            
            # Check if the request was successful
            if response.status_code == 201 or response.status_code == 200:
                pin_data = response.json()
                logging.info(f"Successfully posted to Pinterest. Pin ID: {pin_data.get('id')}")
                return True
            else:
                logging.error(f"Failed to post to Pinterest. Status code: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Error posting to Pinterest: {e}")
            return False
            
    def upload_image(self, image_path):
        """Upload image to Pinterest and get media ID"""
        try:
            # First, get upload parameters from Pinterest
            url = f"{self.api_base_url}/media"
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            # Read image and get its size
            with open(image_path, 'rb') as img_file:
                img_data = img_file.read()
                img_size = len(img_data)
            
            # Request upload parameters
            params = {
                'media_type': 'image'
            }
            
            response = requests.post(url, headers=headers, json=params)
            
            if response.status_code != 201 and response.status_code != 200:
                logging.error(f"Failed to get upload parameters. Status: {response.status_code}, Response: {response.text}")
                return None
                
            upload_data = response.json()
            media_id = upload_data.get('media_id')
            upload_url = upload_data.get('upload_url')
            
            if not media_id or not upload_url:
                logging.error("Missing media_id or upload_url in Pinterest response")
                return None
                
            # Upload the image using the provided URL
            with open(image_path, 'rb') as img_file:
                upload_response = requests.put(
                    upload_url,
                    data=img_file,
                    headers={
                        'Content-Type': 'application/octet-stream',
                        'Content-Length': str(img_size)
                    }
                )
                
            if upload_response.status_code != 200:
                logging.error(f"Failed to upload image. Status: {upload_response.status_code}, Response: {upload_response.text}")
                return None
                
            # Wait for Pinterest to process the image
            time.sleep(3)
            
            # Verify that the media was uploaded successfully
            status_url = f"{self.api_base_url}/media/{media_id}"
            status_response = requests.get(status_url, headers=headers)
            
            if status_response.status_code != 200:
                logging.error(f"Failed to check media status. Status: {status_response.status_code}, Response: {status_response.text}")
                return None
                
            status_data = status_response.json()
            if status_data.get('status') != 'succeeded':
                logging.error(f"Media processing failed or not complete. Status: {status_data.get('status')}")
                return None
                
            return media_id
            
        except Exception as e:
            logging.error(f"Error uploading image to Pinterest: {e}")
            return None
            
    def log_daily_activity(self, products_data, success_count):
        """Log the daily activity for tracking purposes"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            log_data = {
                'date': today,
                'total_products_scraped': len(products_data),
                'successful_pins': success_count,
                'board_id': self.board_id,
                'product_categories': list(set(p['category'] for p in products_data))
            }
            
            # Create logs directory if it doesn't exist
            os.makedirs('logs', exist_ok=True)
            
            # Write to log file
            with open(f"logs/pinterest_activity_{today}.json", 'w') as f:
                json.dump(log_data, f, indent=2)
                
            logging.info(f"Daily activity logged to logs/pinterest_activity_{today}.json")
            
        except Exception as e:
            logging.error(f"Error logging daily activity: {e}")
