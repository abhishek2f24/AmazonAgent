import os
import openai
import requests
import logging
import base64
import json
from PIL import Image, ImageDraw, ImageFont
import io
import textwrap

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ImageGenerator:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        openai.api_key = self.api_key
        
    def generate_product_image(self, product_data):
        """Generate an image for a product using DALL-E"""
        try:
            logging.info(f"Generating image for product: {product_data['title']}")
            
            # Create a prompt for image generation
            prompt = f"Create a professional, high-quality promotional image for an Amazon bestseller product: {product_data['title']}. Show the product in a clean, attractive setting that highlights its features. Include space for text and marketing elements. Style: modern, commercial, high-quality, product photography."
            
            # Generate image using DALL-E
            response = openai.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            image_url = response.data[0].url
            
            # Download the generated image
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            
            # Enhance the image with product details
            image = Image.open(io.BytesIO(image_response.content))
            
            # Add product details to the image
            modified_image = self.add_product_details(image, product_data)
            
            # Save to a temporary file
            output_filename = f"product_image_{product_data['title'][:20].replace(' ', '_')}.png"
            modified_image.save(output_filename)
            
            logging.info(f"Successfully generated and saved image to {output_filename}")
            return output_filename
            
        except Exception as e:
            logging.error(f"Error generating image: {e}")
            # Create a fallback image with just text
            return self.create_fallback_image(product_data)
    
    def add_product_details(self, image, product_data):
        """Add product details to the image"""
        try:
            draw = ImageDraw.Draw(image)
            width, height = image.size
            
            # Try to load a nice font, fall back to default if not available
            try:
                title_font = ImageFont.truetype("Arial.ttf", 40)
                price_font = ImageFont.truetype("Arial.ttf", 50)
                subtitle_font = ImageFont.truetype("Arial.ttf", 30)
            except IOError:
                title_font = ImageFont.load_default()
                price_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
            
            # Add semi-transparent overlay for text readability
            overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle([(0, height - 300), (width, height)], fill=(0, 0, 0, 180))
            
            # Add Amazon bestseller badge at top
            badge_overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
            badge_draw = ImageDraw.Draw(badge_overlay)
            badge_draw.rectangle([(0, 0), (width, 80)], fill=(254, 189, 105, 230))
            badge_text = f"AMAZON BESTSELLER - {product_data['category']}"
            badge_draw.text((width//2, 40), badge_text, fill=(0, 0, 0), font=subtitle_font, anchor="mm")
            
            # Composite the images
            image = Image.alpha_composite(image.convert('RGBA'), overlay)
            image = Image.alpha_composite(image, badge_overlay)
            
            # Add product title - wrap text for better appearance
            title = product_data['title']
            wrapped_title = textwrap.fill(title, width=30)
            draw = ImageDraw.Draw(image)
            draw.text((width//2, height - 200), wrapped_title, fill=(255, 255, 255), font=title_font, anchor="mm", align="center")
            
            # Add price with emphasis
            draw.text((width//2, height - 100), product_data['price'], fill=(254, 189, 105), font=price_font, anchor="mm")
            
            # Add a call to action
            draw.text((width//2, height - 50), "Check it out on Amazon", fill=(255, 255, 255), font=subtitle_font, anchor="mm")
            
            return image.convert('RGB')  # Convert back to RGB for saving as JPG
            
        except Exception as e:
            logging.error(f"Error adding product details to image: {e}")
            return image.convert('RGB')
    
    def create_fallback_image(self, product_data):
        """Create a simple fallback image with product details"""
        try:
            # Create a blank image
            image = Image.new('RGB', (1024, 1024), color=(30, 30, 30))
            draw = ImageDraw.Draw(image)
            
            try:
                title_font = ImageFont.truetype("Arial.ttf", 40)
                price_font = ImageFont.truetype("Arial.ttf", 60)
                subtitle_font = ImageFont.truetype("Arial.ttf", 30)
            except IOError:
                title_font = ImageFont.load_default()
                price_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
            
            # Add Amazon bestseller badge
            draw.rectangle([(0, 0), (1024, 80)], fill=(254, 189, 105))
            badge_text = f"AMAZON BESTSELLER - {product_data['category']}"
            draw.text((512, 40), badge_text, fill=(0, 0, 0), font=subtitle_font, anchor="mm")
            
            # Add product title - wrapped
            title = product_data['title']
            wrapped_title = textwrap.fill(title, width=30)
            draw.text((512, 400), wrapped_title, fill=(255, 255, 255), font=title_font, anchor="mm", align="center")
            
            # Add price with emphasis
            draw.text((512, 600), product_data['price'], fill=(254, 189, 105), font=price_font, anchor="mm")
            
            # Add a call to action
            draw.text((512, 800), "Check it out on Amazon", fill=(255, 255, 255), font=subtitle_font, anchor="mm")
            
            # Save to a temporary file
            output_filename = f"fallback_image_{product_data['title'][:20].replace(' ', '_')}.png"
            image.save(output_filename)
            
            logging.info(f"Created fallback image and saved to {output_filename}")
            return output_filename
            
        except Exception as e:
            logging.error(f"Error creating fallback image: {e}")
            # If all else fails, return None and the caller will need to handle this
            return None
            
    def generate_seo_content(self, product_data):
        """Generate SEO-optimized title and description for Pinterest"""
        try:
            logging.info(f"Generating SEO content for product: {product_data['title']}")
            
            # Generate SEO content using ChatGPT
            prompt = f"""
            Create SEO-optimized Pinterest content for this Amazon bestseller product:
            
            Product: {product_data['title']}
            Price: {product_data['price']}
            Category: {product_data['category']}
            
            Provide:
            1. A catchy, SEO-rich Pinterest title (max 100 characters)
            2. A compelling Pinterest description with relevant hashtags (max 500 characters)
            3. 5 relevant SEO keywords
            
            Format your response as JSON with keys: 'title', 'description', 'keywords'
            """
            
            response = openai.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are a professional e-commerce marketer specializing in Pinterest SEO."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=1000
                    )

            
            seo_content = json.loads(response.choices[0].message.content)
            logging.info("Successfully generated SEO content")
            return seo_content
            
        except Exception as e:
            logging.error(f"Error generating SEO content: {e}")
            # Provide fallback SEO content
            return {
                'title': f"Amazon Bestseller: {product_data['title'][:80]}",
                'description': f"Check out this top-rated {product_data['category']} product on Amazon! Currently priced at {product_data['price']}. #AmazonBestseller #{product_data['category'].replace(' ', '')} #DealsAndSteals #MustHaveProducts",
                'keywords': ['Amazon Bestseller', product_data['category'], 'Top Rated Products', 'Amazon Deals', 'Must Have Products']
            }
