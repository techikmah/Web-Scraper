"""
Advanced Web Scraper - Professional Implementation
Features:
- CSS and XPath selectors
- JavaScript rendering (Selenium/Playwright)
- Image scraping and downloading
- Proxy rotation with health checks
- Authentication support
- Rate limiting and retry logic
- User-Agent rotation
- Cookie/session management
- Pagination support
- Data validation and cleaning
- Multiple output formats (JSON, CSV, Excel, XML, SQLite)
- Incremental scraping
- Comprehensive error handling
"""

import requests
from bs4 import BeautifulSoup
from lxml import html as lxml_html
import json
import csv
import pandas as pd
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
import random
import time
import os
import re
import sqlite3
from typing import List, Dict, Optional, Callable
import logging
from datetime import datetime
from collections import deque
import hashlib
from dataclasses import dataclass, asdict
import xml.etree.ElementTree as ET

# Optional imports for advanced features
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ScrapingStats:
    """Track scraping statistics"""
    total_pages: int = 0
    successful_pages: int = 0
    failed_pages: int = 0
    total_items: int = 0
    images_downloaded: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def to_dict(self):
        return asdict(self)


class RateLimiter:
    """Rate limiter with exponential backoff"""
    
    def __init__(self, max_requests_per_second: float = 2.0):
        self.max_requests_per_second = max_requests_per_second
        self.min_delay = 1.0 / max_requests_per_second
        self.last_request_time = 0
        self.request_times = deque(maxlen=10)
    
    def wait(self):
        """Wait if necessary to respect rate limit"""
        current_time = time.time()
        if self.last_request_time > 0:
            elapsed = current_time - self.last_request_time
            if elapsed < self.min_delay:
                time.sleep(self.min_delay - elapsed)
        
        self.last_request_time = time.time()
        self.request_times.append(self.last_request_time)


class RetryHandler:
    """Handle retries with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    def execute(self, func: Callable, *args, **kwargs):
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries} attempts failed")
        
        raise last_exception


class UserAgentRotator:
    """Rotate User-Agent strings"""
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    @staticmethod
    def get_random():
        return random.choice(UserAgentRotator.USER_AGENTS)


class ProxyManager:
    """Manage proxy rotation with health checks"""
    
    def __init__(self, proxies: List[str] = None):
        self.proxies = proxies or []
        self.proxy_health = {proxy: {'success': 0, 'failures': 0, 'last_check': None} 
                            for proxy in self.proxies}
        self.current_proxy_index = 0
    
    def get_proxy(self) -> Optional[Dict]:
        """Get next proxy in rotation"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        
        return {
            'http': proxy,
            'https': proxy
        }
    
    def mark_success(self, proxy: str):
        """Mark proxy as successful"""
        if proxy in self.proxy_health:
            self.proxy_health[proxy]['success'] += 1
    
    def mark_failure(self, proxy: str):
        """Mark proxy as failed"""
        if proxy in self.proxy_health:
            self.proxy_health[proxy]['failures'] += 1
    
    def get_healthiest(self) -> Optional[str]:
        """Get healthiest proxy"""
        if not self.proxies:
            return None
        
        best_proxy = None
        best_score = float('-inf')
        
        for proxy in self.proxies:
            health = self.proxy_health[proxy]
            score = health['success'] - health['failures'] * 2
            if score > best_score:
                best_score = score
                best_proxy = proxy
        
        return best_proxy


class DataValidator:
    """Validate and clean scraped data"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean text data"""
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters if needed
        return text.strip()
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def clean_data(data: Dict) -> Dict:
        """Clean all data in dictionary"""
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, str):
                cleaned[key] = DataValidator.clean_text(value)
            elif isinstance(value, list):
                cleaned[key] = [DataValidator.clean_text(str(v)) if isinstance(v, str) else v 
                               for v in value]
            else:
                cleaned[key] = value
        return cleaned


class WebScraper:
    """
    Advanced web scraper with professional features
    """
    
    def __init__(self, config: Dict, progress_callback: Optional[Callable] = None):
        """
        Initialize scraper with configuration
        
        Args:
            config: Dictionary containing scraper configuration
            progress_callback: Optional callback function for progress updates
        """
        self.config = config
        self.session = requests.Session()
        self.results = []
        self.images_downloaded = []
        self.stats = ScrapingStats()
        self.progress_callback = progress_callback
        
        # Initialize components
        self.rate_limiter = RateLimiter(
            max_requests_per_second=config.get('maxRequestsPerSecond', 2.0)
        )
        self.retry_handler = RetryHandler(
            max_retries=config.get('maxRetries', 3),
            base_delay=config.get('retryDelay', 1.0)
        )
        self.proxy_manager = ProxyManager(config.get('proxies', []))
        self.validator = DataValidator()
        
        # Set initial headers with random User-Agent
        self.update_headers()
        
        # JavaScript rendering
        self.use_js_rendering = config.get('useJavaScriptRendering', False)
        self.js_engine = config.get('jsEngine', 'playwright')  # 'playwright' or 'selenium'
        self.driver = None
        self.playwright = None
        self.browser = None
        self.page = None
        
        # Pagination
        self.pagination_config = config.get('pagination', {})
        
        # Incremental scraping
        self.incremental = config.get('incrementalScraping', False)
        self.data_hash = set()
    
    def update_headers(self):
        """Update session headers with random User-Agent"""
        self.session.headers.update({
            'User-Agent': UserAgentRotator.get_random(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        })
    
    def load_proxies(self, proxy_file: str = None) -> List[str]:
        """Load proxies from file or config"""
        proxies = []
        
        if proxy_file and os.path.exists(proxy_file):
            with open(proxy_file, 'r') as f:
                proxies = [line.strip() for line in f if line.strip()]
        elif 'proxies' in self.config:
            proxies = self.config['proxies']
        
        self.proxy_manager = ProxyManager(proxies)
        logger.info(f"Loaded {len(proxies)} proxies")
        return proxies
    
    def get_proxy(self) -> Optional[Dict]:
        """Get proxy for request"""
        return self.proxy_manager.get_proxy()
    
    def load_credentials(self, creds_file: str = None) -> List[Dict]:
        """Load login credentials from file or config"""
        credentials = []
        
        if creds_file and os.path.exists(creds_file):
            with open(creds_file, 'r') as f:
                reader = csv.DictReader(f)
                credentials = list(reader)
        elif 'credentials' in self.config:
            for cred in self.config['credentials']:
                if isinstance(cred, str) and ',' in cred:
                    parts = cred.split(',')
                    credentials.append({
                        'username': parts[0].strip(),
                        'password': parts[1].strip()
                    })
                elif isinstance(cred, dict):
                    credentials.append(cred)
        
        logger.info(f"Loaded {len(credentials)} credential sets")
        return credentials
    
    def login(self, login_url: str = None, username_field: str = 'username', 
              password_field: str = 'password') -> bool:
        """Handle login if credentials provided"""
        if not hasattr(self, 'credentials') or not self.credentials:
            return False
        
        cred = self.credentials[0]
        login_url = login_url or self.config.get('loginUrl', self.config.get('url', '') + '/login')
        
        login_data = {
            username_field: cred.get('username', cred.get('user', '')),
            password_field: cred.get('password', cred.get('pass', ''))
        }
        
        try:
            response = self.session.post(
                login_url,
                data=login_data,
                proxies=self.get_proxy(),
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info("Login successful")
                return True
            else:
                logger.warning(f"Login failed with status code: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def init_js_engine(self):
        """Initialize JavaScript rendering engine"""
        if not self.use_js_rendering:
            return
        
        try:
            if self.js_engine == 'playwright' and PLAYWRIGHT_AVAILABLE:
                self.playwright = sync_playwright().start()
                self.browser = self.playwright.chromium.launch(headless=True)
                self.page = self.browser.new_page()
                logger.info("Playwright initialized")
            elif self.js_engine == 'selenium' and SELENIUM_AVAILABLE:
                options = ChromeOptions()
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                self.driver = webdriver.Chrome(options=options)
                logger.info("Selenium initialized")
            else:
                logger.warning("JavaScript rendering requested but engine not available")
                self.use_js_rendering = False
        except Exception as e:
            logger.error(f"Failed to initialize JS engine: {e}")
            self.use_js_rendering = False
    
    def close_js_engine(self):
        """Close JavaScript rendering engine"""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            if self.driver:
                self.driver.quit()
        except:
            pass
    
    def get_page_content(self, url: str) -> Optional[str]:
        """Get page content, using JS rendering if enabled"""
        if self.use_js_rendering:
            try:
                if self.js_engine == 'playwright' and self.page:
                    self.page.goto(url, wait_until='networkidle', timeout=30000)
                    return self.page.content()
                elif self.js_engine == 'selenium' and self.driver:
                    self.driver.get(url)
                    time.sleep(2)  # Wait for JS to load
                    return self.driver.page_source
            except Exception as e:
                logger.error(f"JS rendering error: {e}")
                # Fallback to regular request
                pass
        
        # Regular HTTP request
        def make_request():
            self.rate_limiter.wait()
            proxy = self.get_proxy()
            response = self.session.get(url, proxies=proxy, timeout=30)
            response.raise_for_status()
            return response.text
        
        try:
            return self.retry_handler.execute(make_request)
        except Exception as e:
            logger.error(f"Request error for {url}: {e}")
            return None
    
    def extract_with_css(self, soup: BeautifulSoup, selector: str, attribute: str = None) -> List[str]:
        """Extract data using CSS selector"""
        try:
            elements = soup.select(selector)
            if attribute:
                return [elem.get(attribute, '') for elem in elements if elem.get(attribute)]
            return [elem.get_text(strip=True) for elem in elements]
        except Exception as e:
            logger.error(f"CSS selector error for '{selector}': {e}")
            return []
    
    def extract_with_xpath(self, content: str, xpath: str) -> List[str]:
        """Extract data using XPath"""
        try:
            tree = lxml_html.fromstring(content)
            elements = tree.xpath(xpath)
            return [elem.text_content().strip() if hasattr(elem, 'text_content') 
                   else str(elem).strip() for elem in elements]
        except Exception as e:
            logger.error(f"XPath error for '{xpath}': {e}")
            return []
    
    def download_image(self, img_url: str, save_dir: str = 'images') -> Optional[str]:
        """Download image and return local path"""
        try:
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            filename = os.path.basename(urlparse(img_url).path)
            if not filename or '.' not in filename:
                ext = img_url.split('.')[-1].split('?')[0]
                filename = f"image_{len(self.images_downloaded)}.{ext if len(ext) < 5 else 'jpg'}"
            
            filepath = os.path.join(save_dir, filename)
            
            response = self.session.get(img_url, timeout=30, stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded image: {filename}")
            self.stats.images_downloaded += 1
            return filepath
            
        except Exception as e:
            logger.error(f"Error downloading image {img_url}: {e}")
            return None
    
    def get_pagination_urls(self, base_url: str) -> List[str]:
        """Generate pagination URLs"""
        if not self.pagination_config:
            return [base_url]
        
        urls = []
        pagination_type = self.pagination_config.get('type', 'query')
        start_page = self.pagination_config.get('startPage', 1)
        end_page = self.pagination_config.get('endPage', 1)
        param_name = self.pagination_config.get('paramName', 'page')
        
        for page in range(start_page, end_page + 1):
            if pagination_type == 'query':
                parsed = urlparse(base_url)
                query = parse_qs(parsed.query)
                query[param_name] = [str(page)]
                new_query = urlencode(query, doseq=True)
                new_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"
                urls.append(new_url)
            elif pagination_type == 'path':
                urls.append(f"{base_url.rstrip('/')}/page/{page}")
        
        return urls
    
    def is_duplicate(self, data: Dict) -> bool:
        """Check if data is duplicate (for incremental scraping)"""
        if not self.incremental:
            return False
        
        # Create hash of data
        data_str = json.dumps(data, sort_keys=True)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()
        
        if data_hash in self.data_hash:
            return True
        
        self.data_hash.add(data_hash)
        return False
    
    def scrape_items(self, url: str, download_images: bool = False) -> Optional[List[Dict]]:
        """
        Scrape identical items from a single page (e.g., products, articles)
        
        This method finds all item containers and extracts fields from each item.
        Useful for product listings, article lists, etc.
        
        Args:
            url: URL to scrape
            download_images: Whether to download images locally
            
        Returns:
            List of dictionaries, each representing one item
        """
        try:
            logger.info(f"Scraping items from: {url}")
            
            content = self.get_page_content(url)
            if not content:
                self.stats.failed_pages += 1
                return None
            
            soup = BeautifulSoup(content, 'html.parser')
            items = []
            
            # Get item-based scraping config
            item_config = self.config.get('itemScraping', {})
            container_selector = item_config.get('containerSelector', '')
            container_type = item_config.get('containerType', 'css')
            field_selectors = item_config.get('fieldSelectors', [])
            
            if not container_selector:
                logger.error("Container selector is required for item-based scraping")
                return None
            
            # Find all item containers and prepare both BS4 and lxml versions
            tree = lxml_html.fromstring(content)
            
            if container_type == 'css':
                containers_bs4 = soup.select(container_selector)
                # Get corresponding lxml elements by converting CSS selector to XPath approximation
                containers_lxml = []
                # Simple approach: convert CSS class/id selector to XPath
                xpath_selector = container_selector
                if container_selector.startswith('.'):
                    class_name = container_selector[1:]
                    xpath_selector = f"//*[contains(@class, '{class_name}')]"
                elif container_selector.startswith('#'):
                    id_name = container_selector[1:]
                    xpath_selector = f"//*[@id='{id_name}']"
                else:
                    # Try as tag name
                    xpath_selector = f"//{container_selector}"
                
                try:
                    containers_lxml = tree.xpath(xpath_selector)
                    # Ensure same length
                    while len(containers_lxml) < len(containers_bs4):
                        containers_lxml.append(None)
                    containers_lxml = containers_lxml[:len(containers_bs4)]
                except:
                    containers_lxml = [None] * len(containers_bs4)
            else:  # xpath
                containers_lxml = tree.xpath(container_selector)
                # Convert to BeautifulSoup for CSS field selectors
                containers_bs4 = []
                for lxml_cont in containers_lxml:
                    try:
                        cont_html = lxml_html.tostring(lxml_cont, encoding='unicode')
                        containers_bs4.append(BeautifulSoup(cont_html, 'html.parser'))
                    except Exception as e:
                        logger.warning(f"Error converting container to BS4: {e}")
                        containers_bs4.append(None)
            
            num_containers = len(containers_bs4) if container_type == 'css' else len(containers_lxml)
            logger.info(f"Found {num_containers} item containers")
            
            # Extract data from each container
            for idx in range(num_containers):
                item_data = {
                    'item_index': idx + 1,
                    'url': url,
                    'scraped_at': datetime.now().isoformat()
                }
                
                # Get container in appropriate format
                if container_type == 'css':
                    container_bs4 = containers_bs4[idx] if idx < len(containers_bs4) else None
                    container_lxml = containers_lxml[idx] if idx < len(containers_lxml) else None
                else:
                    container_lxml = containers_lxml[idx] if idx < len(containers_lxml) else None
                    container_bs4 = containers_bs4[idx] if idx < len(containers_bs4) else None
                
                # Extract each field from the container
                for field_config in field_selectors:
                    field_name = field_config.get('name', 'unnamed')
                    field_selector = field_config.get('selector', '')
                    field_type = field_config.get('type', 'css')
                    attribute = field_config.get('attribute', None)
                    is_required = field_config.get('required', False)
                    
                    if not field_selector:
                        continue
                    
                    try:
                        if field_type == 'css':
                            # Use BeautifulSoup container
                            if container_bs4 and hasattr(container_bs4, 'select'):
                                elements = container_bs4.select(field_selector)
                            elif container_bs4 and hasattr(container_bs4, 'select_one'):
                                element = container_bs4.select_one(field_selector)
                                elements = [element] if element else []
                            else:
                                elements = []
                            
                            if elements:
                                if attribute:
                                    value = elements[0].get(attribute, '')
                                else:
                                    value = elements[0].get_text(strip=True)
                            else:
                                value = ''
                        else:  # xpath
                            # Use lxml container
                            if container_lxml:
                                try:
                                    # Use relative xpath (starts with .// or ./)
                                    if field_selector.startswith('.//') or field_selector.startswith('./'):
                                        elements = container_lxml.xpath(field_selector)
                                    elif field_selector.startswith('//'):
                                        # Absolute xpath - search within container
                                        elements = container_lxml.xpath(f'.{field_selector}')
                                    else:
                                        # Relative path without .// prefix
                                        elements = container_lxml.xpath(f'.//{field_selector}')
                                except Exception as xpath_err:
                                    logger.warning(f"XPath error for '{field_selector}': {xpath_err}")
                                    elements = []
                            else:
                                elements = []
                            
                            if elements:
                                try:
                                    if hasattr(elements[0], 'text_content'):
                                        value = elements[0].text_content().strip()
                                    elif hasattr(elements[0], 'text'):
                                        value = str(elements[0].text).strip()
                                    elif isinstance(elements[0], str):
                                        value = elements[0].strip()
                                    else:
                                        value = str(elements[0]).strip()
                                except:
                                    value = str(elements[0]) if elements else ''
                            else:
                                value = ''
                        
                        # Handle relative URLs for links and images
                        if attribute in ['href', 'src', 'data-src'] and value:
                            if not value.startswith(('http://', 'https://')):
                                value = urljoin(url, value)
                        
                        item_data[field_name] = value
                        
                    except Exception as e:
                        logger.warning(f"Error extracting field '{field_name}' from item {idx + 1}: {e}")
                        if is_required:
                            # Skip this item if required field is missing
                            item_data = None
                            break
                        item_data[field_name] = ''
                
                # Only add item if it has data (or if required fields are present)
                if item_data:
                    # Clean and validate data
                    item_data = self.validator.clean_data(item_data)
                    
                    # Check for duplicates
                    if not self.is_duplicate(item_data):
                        items.append(item_data)
                        self.stats.total_items += 1
                    else:
                        logger.info(f"Skipping duplicate item {idx + 1}")
            
            # Handle images if enabled
            if self.config.get('scrapeImages', False) and items:
                img_selector = self.config.get('imageSelector', 'img')
                for item in items:
                    # Try to find image in item data
                    image_url = None
                    for key, value in item.items():
                        if 'image' in key.lower() or 'img' in key.lower():
                            if isinstance(value, str) and value.startswith(('http://', 'https://')):
                                image_url = value
                                break
                    
                    if image_url and download_images:
                        local_path = self.download_image(image_url)
                        if local_path:
                            item['image_local_path'] = local_path
            
            logger.info(f"Extracted {len(items)} items from page")
            self.stats.successful_pages += 1
            return items
            
        except Exception as e:
            logger.error(f"Error scraping items from {url}: {e}")
            self.stats.failed_pages += 1
            return None
    
    def scrape_page(self, url: str, download_images: bool = False) -> Optional[Dict]:
        """
        Scrape a single page
        
        Supports two modes:
        1. Regular scraping: Extract fields from entire page
        2. Item-based scraping: Extract identical items (products, articles, etc.)
        """
        # Check if item-based scraping is enabled
        if self.config.get('itemScraping', {}).get('enabled', False):
            items = self.scrape_items(url, download_images)
            if items:
                # Return as a page result with items
                return {
                    'url': url,
                    'scraped_at': datetime.now().isoformat(),
                    'items': items,
                    'items_count': len(items)
                }
            return None
        
        # Regular scraping mode
        try:
            logger.info(f"Scraping: {url}")
            
            content = self.get_page_content(url)
            if not content:
                self.stats.failed_pages += 1
                return None
            
            soup = BeautifulSoup(content, 'html.parser')
            page_data = {'url': url, 'scraped_at': datetime.now().isoformat()}
            
            # Extract data using configured selectors
            for selector_config in self.config.get('selectors', []):
                name = selector_config.get('name', 'unnamed')
                selector = selector_config.get('selector', '')
                selector_type = selector_config.get('type', 'css')
                attribute = selector_config.get('attribute', None)
                
                if not selector:
                    continue
                
                if selector_type == 'css':
                    values = self.extract_with_css(soup, selector, attribute)
                else:  # xpath
                    values = self.extract_with_xpath(content, selector)
                
                page_data[name] = values
                self.stats.total_items += len(values)
                logger.info(f"Extracted {len(values)} items for '{name}'")
            
            # Scrape images if enabled
            if self.config.get('scrapeImages', False):
                img_selector = self.config.get('imageSelector', 'img')
                images = soup.select(img_selector)
                
                image_urls = []
                for img in images:
                    img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                    if img_url:
                        full_url = urljoin(url, img_url)
                        image_urls.append(full_url)
                        
                        if download_images:
                            local_path = self.download_image(full_url)
                            if local_path:
                                self.images_downloaded.append(local_path)
                
                page_data['images'] = image_urls
                logger.info(f"Found {len(image_urls)} images")
            
            # Clean and validate data
            page_data = self.validator.clean_data(page_data)
            
            # Check for duplicates
            if self.is_duplicate(page_data):
                logger.info("Skipping duplicate data")
                return None
            
            self.stats.successful_pages += 1
            return page_data
            
        except Exception as e:
            logger.error(f"Scraping error for {url}: {e}")
            self.stats.failed_pages += 1
            return None
    
    def save_json(self, data: List[Dict], filename: str = 'scraped_data.json'):
        """Save results as JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(data)} records to {filename}")
    
    def save_csv(self, data: List[Dict], filename: str = 'scraped_data.csv'):
        """Save results as CSV"""
        if not data:
            logger.warning("No data to save")
            return
        
        flattened_data = []
        for item in data:
            flat_item = {}
            for key, value in item.items():
                if isinstance(value, list):
                    flat_item[key] = '|'.join(str(v) for v in value)
                else:
                    flat_item[key] = value
            flattened_data.append(flat_item)
        
        df = pd.DataFrame(flattened_data)
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"Saved {len(flattened_data)} records to {filename}")
    
    def save_excel(self, data: List[Dict], filename: str = 'scraped_data.xlsx'):
        """Save results as Excel"""
        if not data:
            logger.warning("No data to save")
            return
        
        flattened_data = []
        for item in data:
            flat_item = {}
            for key, value in item.items():
                if isinstance(value, list):
                    flat_item[key] = ', '.join(str(v) for v in value)
                else:
                    flat_item[key] = value
            flattened_data.append(flat_item)
        
        df = pd.DataFrame(flattened_data)
        df.to_excel(filename, index=False, engine='openpyxl')
        logger.info(f"Saved {len(flattened_data)} records to {filename}")
    
    def save_xml(self, data: List[Dict], filename: str = 'scraped_data.xml'):
        """Save results as XML"""
        root = ET.Element('scraped_data')
        for item in data:
            record = ET.SubElement(root, 'record')
            for key, value in item.items():
                elem = ET.SubElement(record, key.replace(' ', '_'))
                if isinstance(value, list):
                    elem.text = '|'.join(str(v) for v in value)
                else:
                    elem.text = str(value) if value else ''
        
        tree = ET.ElementTree(root)
        tree.write(filename, encoding='utf-8', xml_declaration=True)
        logger.info(f"Saved {len(data)} records to {filename}")
    
    def save_sqlite(self, data: List[Dict], filename: str = 'scraped_data.db'):
        """Save results as SQLite database"""
        if not data:
            logger.warning("No data to save")
            return
        
        conn = sqlite3.connect(filename)
        cursor = conn.cursor()
        
        # Create table
        if data:
            first_item = data[0]
            columns = []
            for key in first_item.keys():
                col_name = key.replace(' ', '_').replace('-', '_')
                columns.append(f"{col_name} TEXT")
            
            table_name = 'scraped_data'
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            cursor.execute(f"CREATE TABLE {table_name} ({', '.join(columns)})")
            
            # Insert data
            for item in data:
                keys = list(item.keys())
                placeholders = ','.join(['?' for _ in keys])
                col_names = ','.join([k.replace(' ', '_').replace('-', '_') for k in keys])
                values = []
                for key in keys:
                    value = item[key]
                    if isinstance(value, list):
                        values.append('|'.join(str(v) for v in value))
                    else:
                        values.append(str(value) if value else '')
                
                cursor.execute(f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})", values)
        
        conn.commit()
        conn.close()
        logger.info(f"Saved {len(data)} records to {filename}")
    
    def save_results(self, data: List[Dict]):
        """Save results in specified format"""
        output_format = self.config.get('outputFormat', 'json')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if output_format == 'json':
            filename = f'scraped_data_{timestamp}.json'
            self.save_json(data, filename)
        elif output_format == 'csv':
            filename = f'scraped_data_{timestamp}.csv'
            self.save_csv(data, filename)
        elif output_format == 'excel':
            filename = f'scraped_data_{timestamp}.xlsx'
            self.save_excel(data, filename)
        elif output_format == 'xml':
            filename = f'scraped_data_{timestamp}.xml'
            self.save_xml(data, filename)
        elif output_format == 'sqlite':
            filename = f'scraped_data_{timestamp}.db'
            self.save_sqlite(data, filename)
        else:
            logger.error(f"Unknown output format: {output_format}")
    
    def run(self, urls: List[str] = None, delay: float = 1.0):
        """
        Main scraping workflow
        
        Args:
            urls: List of URLs to scrape (if None, uses config URL)
            delay: Delay between requests in seconds
        """
        logger.info("="*50)
        logger.info("Starting Advanced Web Scraper")
        logger.info("="*50)
        
        self.stats.start_time = datetime.now()
        
        # Initialize JS engine if needed
        if self.use_js_rendering:
            self.init_js_engine()
        
        try:
            # Load proxies and credentials
            self.proxies = self.load_proxies()
            self.credentials = self.load_credentials()
            
            # Login if credentials provided
            if self.credentials:
                self.login()
            
            # Get URLs to scrape
            if urls is None:
                base_url = self.config.get('url', '')
                if self.pagination_config:
                    urls = self.get_pagination_urls(base_url)
                else:
                    urls = [base_url]
            
            self.stats.total_pages = len(urls)
            
            # Scrape each URL
            for idx, url in enumerate(urls):
                if not url:
                    continue
                
                if self.progress_callback:
                    self.progress_callback({
                        'current': idx + 1,
                        'total': len(urls),
                        'url': url,
                        'status': 'scraping'
                    })
                
                result = self.scrape_page(url, download_images=self.config.get('downloadImages', False))
                
                if result:
                    # For item-based scraping, result contains items list
                    if 'items' in result:
                        # Flatten items into results
                        for item in result.get('items', []):
                            self.results.append(item)
                    else:
                        self.results.append(result)
                
                # Delay between requests
                if idx < len(urls) - 1:
                    time.sleep(delay)
            
            # Save results
            if self.results:
                self.save_results(self.results)
                logger.info(f"Successfully scraped {len(self.results)} pages")
                logger.info(f"Downloaded {len(self.images_downloaded)} images")
            else:
                logger.warning("No results to save")
        
        finally:
            # Close JS engine
            self.close_js_engine()
            
            self.stats.end_time = datetime.now()
            duration = (self.stats.end_time - self.stats.start_time).total_seconds()
            
            logger.info("="*50)
            logger.info("Scraping Completed")
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info(f"Stats: {self.stats.to_dict()}")
            logger.info("="*50)


# Example usage
if __name__ == "__main__":
    config = {
        'url': 'https://example.com',
        'selectors': [
            {
                'name': 'title',
                'selector': 'h1',
                'type': 'css'
            },
            {
                'name': 'paragraphs',
                'selector': 'p',
                'type': 'css'
            }
        ],
        'scrapeImages': True,
        'imageSelector': 'img',
        'outputFormat': 'json',  # Options: 'json', 'csv', 'excel', 'xml', 'sqlite'
        'useJavaScriptRendering': False,
        'jsEngine': 'playwright',
        'maxRequestsPerSecond': 2.0,
        'maxRetries': 3,
        'pagination': {
            'type': 'query',
            'startPage': 1,
            'endPage': 5,
            'paramName': 'page'
        },
        'incrementalScraping': False,
        'proxies': [],
        'credentials': []
    }
    
    scraper = WebScraper(config)
    scraper.run()
