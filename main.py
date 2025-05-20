import os
import logging
import json
from dotenv import load_dotenv
from scripts.amazon_scrapper import AmazonScraper
from scripts.image_generator import ImageGenerator
from scripts.pinterest_poster import PinterestPoster
import time
# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automation.log"),
        logging.StreamHandler()
    ]
)

def main() -> None:
    try:
        # Load environment variables
        load_dotenv()
        
        # Check if required environment variables are set
        required_vars = ['OPENAI_API_KEY', 'PINTEREST_ACCESS_TOKEN', 'PINTEREST_BOARD_ID']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            logging.error("Missing required environment variables: %s", ', '.join(missing_vars))
            logging.info("Please set them in a .env file or in your GitHub repository secrets.")
            return
        
        # Initialize components
        scraper = AmazonScraper()
        image_generator = ImageGenerator()
        pinterest_poster = PinterestPoster()
        
        # 1. Scrape Amazon bestsellers
        logging.info("Starting Amazon bestseller scraping...")
        products = scraper.scrape_bestsellers()
        
        if not products or len(products) == 0:
            logging.error("No products scraped from Amazon. Aborting.")
            return
            
        logging.info(f"Successfully scraped {len(products)} products from Amazon")
        
        # Take top 5 products (or fewer if less than 5 were scraped)
        top_products = products[:5]
        
        # Track successful pins
        successful_pins = 0
        
        # 2 & 3. For each product, generate image and post to Pinterest
        for product in top_products:
            try:
                # Generate SEO content
                seo_content = image_generator.generate_seo_content(product)
                time.sleep(2) 
                
                # Generate image
                image_path = image_generator.generate_product_image(product)
                time.sleep(2) 
                
                if not image_path:
                    logging.error(f"Failed to generate image for product: {product['title']}")
                    continue
                
                # Post to Pinterest
                success = pinterest_poster.post_to_pinterest(image_path, product, seo_content)
                
                if success:
                    successful_pins += 1
                    
                # Clean up temporary image file
                try:
                    os.remove(image_path)
                except Exception as e:
                    logging.warning(f"Failed to remove temporary image file {image_path}: {e}")
                    
            except Exception as e:
                logging.error(f"Error processing product {product['title']}: {e}")
                continue
        
        # Log daily activity
        pinterest_poster.log_daily_activity(top_products, successful_pins)
        
        logging.info(f"Automation completed: {successful_pins}/{len(top_products)} products successfully posted to Pinterest")
        
    except Exception as e:
        logging.error(f"Automation failed with error: {e}")

if __name__ == "__main__":
    main()
