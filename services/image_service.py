import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from flask import current_app, session
import json
import logging
import random
import time

class ImageService:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
        ]
        self._update_headers()

    def _update_headers(self):
        """Update headers with a random user agent"""
        self.headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }

    def extract_images(self, url):
        """Extract images from a given URL"""
        try:
            # Validate URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            # Check if it's a Shopify store
            is_shopify = '.myshopify.com' in url or self._is_shopify_store(url)
            
            if is_shopify:
                current_app.logger.info(f"Detected Shopify store: {url}")
                return self._extract_images_shopify(url)
            
            # For non-Shopify sites
            self._update_headers()  # Rotate user agent
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Add a small delay to be polite
            time.sleep(random.uniform(1, 2))
            
            soup = BeautifulSoup(response.text, 'html.parser')
            images = []
            seen_urls = set()  # To avoid duplicates

            # Helper function to get image dimensions
            def get_image_dimensions(img_tag):
                width = img_tag.get('width')
                height = img_tag.get('height')
                try:
                    return {
                        'width': int(width) if width else None,
                        'height': int(height) if height else None
                    }
                except (ValueError, TypeError):
                    return {'width': None, 'height': None}

            # Process standard img tags
            for img in soup.find_all('img'):
                src = img.get('src', img.get('data-src', ''))
                if not src or src.startswith('data:'):
                    continue
                
                # Make URL absolute
                src = urljoin(url, src)
                
                # Skip if we've seen this URL
                if src in seen_urls:
                    continue
                seen_urls.add(src)
                
                images.append({
                    'url': src,
                    'alt': img.get('alt', ''),
                    'dimensions': get_image_dimensions(img)
                })

            # Look for images in background styles
            for tag in soup.find_all(['div', 'section', 'a']):
                style = tag.get('style', '')
                if 'background-image' in style:
                    match = re.search(r'url\([\'"]?([^\'"]+)[\'"]?\)', style)
                    if match:
                        src = match.group(1)
                        src = urljoin(url, src)
                        if src not in seen_urls:
                            seen_urls.add(src)
                            images.append({
                                'url': src,
                                'alt': tag.get('aria-label', ''),
                                'dimensions': {'width': None, 'height': None}
                            })

            # Look for images in JSON-LD
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    import json
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        # Extract image URLs from JSON-LD
                        def extract_image_urls(obj):
                            if isinstance(obj, dict):
                                for key, value in obj.items():
                                    if key in ['image', 'thumbnail'] and isinstance(value, str):
                                        src = urljoin(url, value)
                                        if src not in seen_urls:
                                            seen_urls.add(src)
                                            images.append({
                                                'url': src,
                                                'alt': '',
                                                'dimensions': {'width': None, 'height': None}
                                            })
                                    elif isinstance(value, (dict, list)):
                                        extract_image_urls(value)
                            elif isinstance(obj, list):
                                for item in obj:
                                    extract_image_urls(item)
                        
                        extract_image_urls(data)
                except:
                    pass

            # Filter out invalid URLs
            valid_images = []
            for img in images:
                try:
                    parsed = urlparse(img['url'])
                    if parsed.scheme and parsed.netloc:
                        valid_images.append(img)
                except:
                    continue

            current_app.logger.info(f"Extracted {len(valid_images)} images from {url}")
            return valid_images

        except Exception as e:
            current_app.logger.error(f"Error extracting images from {url}: {str(e)}")
            return []
    
    def _is_product_image(self, url, alt):
        """Check if the image is likely a product image"""
        # Skip common non-product images
        skip_patterns = ['logo', 'icon', 'banner', 'background', 'avatar']
        url_lower = url.lower()
        alt_lower = alt.lower()
        
        for pattern in skip_patterns:
            if pattern in url_lower or pattern in alt_lower:
                return False
        
        # Check image dimensions in URL (if available)
        if any(dim in url_lower for dim in ['50x50', '100x100', '32x32']):
            return False
        
        return True

    def _sort_images_by_dimensions(self, images):
        """Sort images by dimensions (largest first)"""
        def get_image_size(img):
            try:
                width = int(img.get('width', '0') or '0')
                height = int(img.get('height', '0') or '0')
                return width * height
            except (ValueError, TypeError):
                return 0
        
        # Split images into two groups: with and without dimensions
        with_dimensions = []
        without_dimensions = []
        
        for img in images:
            if get_image_size(img) > 0:
                with_dimensions.append(img)
            else:
                without_dimensions.append(img)
        
        # Sort images with dimensions by size (largest first)
        with_dimensions.sort(key=get_image_size, reverse=True)
        
        # Return sorted images followed by images without dimensions
        return with_dimensions + without_dimensions
    
    def _process_image(self, img, images, base_url):
        """Process an image element and add it to the images list if valid"""
        try:
            # Try different image source attributes
            src = (img.get('src') or 
                  img.get('data-src') or 
                  img.get('data-lazy-src') or
                  img.get('data-original') or
                  img.get('data-fallback-src') or
                  img.get('data-zoom-image') or
                  img.get('data-large_image') or
                  img.get('data-full-image') or
                  img.get('data-image') or
                  img.get('data-lazy'))
            
            if not src:
                # Try to find image URL in data attributes
                for attr in img.attrs:
                    if 'src' in attr.lower() or 'image' in attr.lower():
                        src = img[attr]
                        break
            
            if src:
                # Handle protocol-relative URLs
                if src.startswith('//'):
                    src = 'https:' + src
                # Handle relative URLs
                elif not bool(urlparse(src).netloc):
                    src = urljoin(base_url, src)
                
                # Skip small images and icons
                if self._is_valid_image(src):
                    # Get srcset if available
                    srcset = img.get('srcset', '')
                    largest_src = self._get_largest_image_from_srcset(srcset, src)
                    
                    # Get dimensions from various attributes
                    width = (img.get('width') or 
                            img.get('data-width') or 
                            img.get('data-original-width'))
                    height = (img.get('height') or 
                             img.get('data-height') or 
                             img.get('data-original-height'))
                    
                    # Try to get dimensions from style attribute
                    if not width or not height:
                        style = img.get('style', '')
                        width_match = re.search(r'width:\s*(\d+)px', style)
                        height_match = re.search(r'height:\s*(\d+)px', style)
                        width = width_match.group(1) if width_match else width
                        height = height_match.group(1) if height_match else height
                    
                    images.append({
                        'url': largest_src,
                        'alt': img.get('alt', ''),
                        'width': str(width) if width else '',
                        'height': str(height) if height else ''
                    })
        except Exception as e:
            current_app.logger.error(f"Error processing image: {str(e)}")
    
    def _get_largest_image_from_srcset(self, srcset, fallback_src):
        """Extract the largest image from srcset attribute"""
        if not srcset:
            return fallback_src
            
        try:
            # Parse srcset entries
            entries = [s.strip() for s in srcset.split(',')]
            max_width = 0
            largest_src = fallback_src
            
            for entry in entries:
                parts = entry.strip().split()
                if len(parts) == 2:
                    src, width = parts
                    # Extract numeric width value
                    width_val = int(''.join(filter(str.isdigit, width)))
                    if width_val > max_width:
                        max_width = width_val
                        largest_src = src
            
            return largest_src
        except:
            return fallback_src
    
    def _is_valid_image(self, url):
        """Check if the image URL is valid and not a small icon"""
        # Skip common icon and placeholder patterns
        skip_patterns = [
            'icon', 'logo', 'placeholder', 'thumbnail',
            'avatar', 'favicon', 'social', 'banner',
            'tracking', 'pixel', 'advertisement',
            'sprite', 'loading', 'blank'
        ]
        url_lower = url.lower()
        
        # Skip obvious non-product images
        if any(pattern in url_lower for pattern in skip_patterns):
            return False
            
        # Check file extension
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        if not any(ext in url_lower for ext in valid_extensions):
            return False
            
        # Additional checks for image quality
        quality_indicators = ['large', 'full', 'zoom', 'high', 'original', 'product', 'hero', '560x560']
        has_quality = any(indicator in url_lower for indicator in quality_indicators)
        
        # Special handling for public.gr images
        is_public_gr = 'webstorage.gr' in url_lower or 'mmimages' in url_lower
        
        # If it's a public.gr image or has quality indicators, consider it valid
        return is_public_gr or has_quality or any(ext in url_lower for ext in valid_extensions) 

    def _is_shopify_store(self, url):
        """Check if the given URL is a Shopify store"""
        try:
            self._update_headers()
            response = requests.get(url, headers=self.headers, timeout=5)
            return any(indicator in response.text.lower() for indicator in [
                'shopify.com',
                'cdn.shopify.com',
                'shopify.theme'
            ])
        except:
            return False

    def _extract_images_shopify(self, url):
        """Extract images from a Shopify store with web search fallback"""
        try:
            # First try direct HTML extraction
            self._update_headers()
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            images = []
            seen_urls = set()

            # Try to get product title and brand
            product_title = None
            product_brand = None

            # Look for product title in meta tags
            meta_title = soup.find('meta', property='og:title')
            if meta_title:
                product_title = meta_title.get('content', '')
            if not product_title:
                title_tag = soup.find('title')
                if title_tag:
                    product_title = title_tag.text.split('|')[0].strip()

            # Look for brand in meta tags
            meta_brand = soup.find('meta', property='og:brand')
            if meta_brand:
                product_brand = meta_brand.get('content', '')

            # If we couldn't find the title in meta tags, try common title selectors
            if not product_title:
                title_selectors = [
                    'h1.product-title',
                    'h1.product__title',
                    'h1.product-single__title',
                    '.product-title',
                    '.product__title',
                    '[data-product-title]'
                ]
                for selector in title_selectors:
                    title_elem = soup.select_one(selector)
                    if title_elem:
                        product_title = title_elem.text.strip()
                        break

            # Try to extract images from HTML first
            shopify_selectors = [
                'img.product__image',
                'img.product-featured-media',
                'img.product-single__image',
                '[data-product-media-type="image"] img',
                '[data-product-single-media-wrapper] img',
                '.product-gallery__image img',
                '.product__media img',
                '.featured-image'
            ]

            for selector in shopify_selectors:
                for img in soup.select(selector):
                    for attr in ['src', 'data-src', 'data-srcset', 'data-original']:
                        src = img.get(attr)
                        if src:
                            if src.startswith('//'):
                                src = 'https:' + src
                            elif not src.startswith('http'):
                                src = urljoin(url, src)
                            if src not in seen_urls:
                                seen_urls.add(src)
                                images.append({
                                    'url': src,
                                    'alt': img.get('alt', ''),
                                    'dimensions': self._get_image_dimensions(img)
                                })

            # If we found images directly, return them
            if images:
                current_app.logger.info(f"Found {len(images)} images directly from HTML")
                return images

            # If we have a product title, try web search
            if product_title:
                current_app.logger.info(f"Trying web search for: {product_title}")
                search_query = product_title
                if product_brand:
                    search_query = f"{product_brand} {search_query}"

                # Try Bing Image Search
                try:
                    bing_images = self._search_bing_images(search_query)
                    if bing_images:
                        current_app.logger.info(f"Found {len(bing_images)} images from Bing")
                        return bing_images
                except Exception as e:
                    current_app.logger.error(f"Bing search failed: {str(e)}")

                # Try Google Custom Search as fallback
                try:
                    google_images = self._search_google_images(search_query)
                    if google_images:
                        current_app.logger.info(f"Found {len(google_images)} images from Google")
                        return google_images
                except Exception as e:
                    current_app.logger.error(f"Google search failed: {str(e)}")

            return []

        except Exception as e:
            current_app.logger.error(f"Error extracting images: {str(e)}")
            return []

    def _search_bing_images(self, query):
        """Search for images using Bing Image Search API"""
        try:
            subscription_key = current_app.config.get('BING_SEARCH_KEY')
            if not subscription_key:
                return []

            search_url = "https://api.bing.microsoft.com/v7.0/images/search"
            headers = {"Ocp-Apim-Subscription-Key": subscription_key}
            params = {
                "q": query,
                "count": 10,
                "imageType": "Shopping"
            }

            response = requests.get(search_url, headers=headers, params=params)
            response.raise_for_status()
            search_results = response.json()

            images = []
            for img in search_results.get("value", []):
                images.append({
                    'url': img['contentUrl'],
                    'alt': img.get('name', ''),
                    'dimensions': {
                        'width': img.get('width'),
                        'height': img.get('height')
                    }
                })

            return images

        except Exception as e:
            current_app.logger.error(f"Bing search error: {str(e)}")
            return []

    def _search_google_images(self, query):
        """Search for images using Google Custom Search API"""
        try:
            api_key = current_app.config.get('GOOGLE_API_KEY')
            cx = current_app.config.get('GOOGLE_SEARCH_CX')
            if not api_key or not cx:
                return []

            search_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': cx,
                'q': query,
                'searchType': 'image',
                'num': 10
            }

            response = requests.get(search_url, params=params)
            response.raise_for_status()
            search_results = response.json()

            images = []
            for item in search_results.get('items', []):
                images.append({
                    'url': item['link'],
                    'alt': item.get('title', ''),
                    'dimensions': {
                        'width': item['image'].get('width'),
                        'height': item['image'].get('height')
                    }
                })

            return images

        except Exception as e:
            current_app.logger.error(f"Google search error: {str(e)}")
            return []

    def _extract_shopify_images(self, data, images, seen_urls, domain):
        """Recursively extract Shopify images from JSON data"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and ('cdn.shopify.com' in value or f'{domain}/cdn/shop/products' in value):
                    if value.startswith('//'):
                        value = 'https:' + value
                    if value not in seen_urls:
                        seen_urls.add(value)
                        images.append({
                            'url': value,
                            'alt': '',
                            'dimensions': {'width': None, 'height': None}
                        })
                elif isinstance(value, (dict, list)):
                    self._extract_shopify_images(value, images, seen_urls, domain)
        elif isinstance(data, list):
            for item in data:
                self._extract_shopify_images(item, images, seen_urls, domain)

    def _get_image_dimensions(self, img):
        """Get image dimensions from img tag"""
        width = img.get('width')
        height = img.get('height')
        try:
            return {
                'width': int(width) if width else None,
                'height': int(height) if height else None
            }
        except (ValueError, TypeError):
            return {'width': None, 'height': None} 