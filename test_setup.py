#!/usr/bin/env python3
"""
Test script to verify the setup is working correctly
Run this to debug issues before running the main bot
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_setup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all required libraries can be imported"""
    logger.info("Testing imports...")
    
    tests = [
        ('requests', 'requests'),
        ('selenium', 'selenium'),
        ('Pinterest', 'py3pin.Pinterest'),
        ('webdriver', 'selenium.webdriver'),
        ('Chrome Options', 'selenium.webdriver.chrome.options'),
    ]
    
    all_passed = True
    
    for name, module in tests:
        try:
            __import__(module)
            logger.info(f"✅ {name}: OK")
        except ImportError as e:
            logger.error(f"❌ {name}: FAILED - {e}")
            all_passed = False
        except Exception as e:
            logger.error(f"❌ {name}: ERROR - {e}")
            all_passed = False
    
    return all_passed

def test_environment_variables():
    """Test if required environment variables are set"""
    logger.info("Testing environment variables...")
    
    required_vars = [
        'PINTEREST_EMAIL',
        'PINTEREST_PASSWORD',
        'AMAZON_AFFILIATE_TAG'
    ]
    
    optional_vars = [
        'PINTEREST_BOARD',
        'MAX_PRODUCTS_PER_CATEGORY',
        'DELAY_BETWEEN_PINS',
        'AMAZON_CATEGORIES'
    ]
    
    all_passed = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var}: Set (length: {len(value)})")
        else:
            logger.error(f"❌ {var}: NOT SET")
            all_passed = False
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var}: {value}")
        else:
            logger.info(f"ℹ️  {var}: Using default")
    
    return all_passed

def test_chrome_setup():
    """Test Chrome and ChromeDriver setup"""
    logger.info("Testing Chrome setup...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        logger.info("Creating Chrome WebDriver...")
        driver = webdriver.Chrome(options=chrome_options)
        
        logger.info("Testing basic navigation...")
        driver.get("https://www.google.com")
        title = driver.title
        
        driver.quit()
        logger.info(f"✅ Chrome setup: OK (page title: {title})")
        return True
        
    except Exception as e:
        logger.error(f"❌ Chrome setup: FAILED - {e}")
        return False

def test_pinterest_connection():
    """Test Pinterest connection"""
    logger.info("Testing Pinterest connection...")
    
    try:
        from py3pin.Pinterest import Pinterest
        
        email = os.getenv('PINTEREST_EMAIL')
        password = os.getenv('PINTEREST_PASSWORD')
        
        if not email or not password:
            logger.error("❌ Pinterest credentials not set")
            return False
        
        logger.info("Connecting to Pinterest...")
        pinterest = Pinterest(email=email, password=password)
        
        logger.info("Getting boards...")
        boards = pinterest.boards()
        
        logger.info(f"✅ Pinterest connection: OK ({len(boards)} boards found)")
        logger.info("Available boards:")
        for board in boards[:5]:  # Show first 5 boards
            logger.info(f"  - {board['name']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Pinterest connection: FAILED - {e}")
        return False

def test_amazon_scraping():
    """Test basic Amazon page access"""
    logger.info("Testing Amazon access...")
    
    try:
        import requests
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Test simple page access
        response = requests.get('https://www.amazon.com/Best-Sellers/zgbs', headers=headers, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"✅ Amazon access: OK (status: {response.status_code})")
            return True
        else:
            logger.error(f"❌ Amazon access: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Amazon access: FAILED - {e}")
        return False

def main():
    """Run all tests"""
    logger.info("="*50)
    logger.info("Amazon to Pinterest Bot - Setup Test")
    logger.info(f"Test started at: {datetime.now()}")
    logger.info("="*50)
    
    tests = [
        ("Import Test", test_imports),
        ("Environment Variables", test_environment_variables),
        ("Chrome Setup", test_chrome_setup),
        ("Pinterest Connection", test_pinterest_connection),
        ("Amazon Access", test_amazon_scraping),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running {test_name}...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("TEST SUMMARY")
    logger.info("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Your setup is ready.")
        return True
    else:
        logger.error("❌ Some tests failed. Please fix the issues before running the bot.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
