import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
from flask import current_app

class PlatformService:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def detect_platform(self, url):
        """
        Detect the e-commerce platform of a given URL
        Returns: dict with platform name and confidence score
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Initialize scores for each platform
            platform_scores = {
                'shopify': 0,
                'wordpress': 0,
                'wix': 0,
                'amazon': 0
            }
            
            # Check URL patterns
            parsed_url = urlparse(url)
            
            # Shopify indicators
            if '/products/' in url:
                platform_scores['shopify'] += 30
            if '.myshopify.com' in url:
                platform_scores['shopify'] += 50
            
            # Check HTML content
            html_content = response.text.lower()
            
            # Shopify detection
            shopify_indicators = [
                'shopify.theme',
                'cdn.shopify.com',
                'shopify.com/s/',
                'shopify-payment-button',
                'data-shopify'
            ]
            for indicator in shopify_indicators:
                if indicator in html_content:
                    platform_scores['shopify'] += 20
            
            # WordPress detection
            wp_indicators = [
                'wp-content',
                'wp-includes',
                'wp-json',
                'wordpress',
                'woocommerce'
            ]
            for indicator in wp_indicators:
                if indicator in html_content:
                    platform_scores['wordpress'] += 20
            
            # Wix detection
            wix_indicators = [
                'wix.com',
                '_wixCssrules',
                'wix-dropdown',
                'wix-image'
            ]
            for indicator in wix_indicators:
                if indicator in html_content:
                    platform_scores['wix'] += 25
            
            # Amazon detection
            amazon_indicators = [
                'amazon-adsystem',
                'amazon.com',
                'amzn.',
                'a-spacing'
            ]
            for indicator in amazon_indicators:
                if indicator in html_content:
                    platform_scores['amazon'] += 25
            
            # Check meta tags
            meta_tags = soup.find_all('meta')
            for tag in meta_tags:
                # Shopify
                if tag.get('property') == 'og:site_name' and 'shopify' in str(tag).lower():
                    platform_scores['shopify'] += 30
                # WordPress
                if tag.get('name') == 'generator' and 'wordpress' in str(tag).lower():
                    platform_scores['wordpress'] += 30
                # Wix
                if 'wix' in str(tag).lower():
                    platform_scores['wix'] += 20
            
            # Check scripts
            scripts = soup.find_all('script')
            for script in scripts:
                src = script.get('src', '')
                # Shopify
                if 'shopify' in str(script).lower():
                    platform_scores['shopify'] += 20
                # WordPress
                if 'wp-' in str(script).lower():
                    platform_scores['wordpress'] += 20
                # Wix
                if 'wix' in str(script).lower():
                    platform_scores['wix'] += 20
                # Amazon
                if 'amazon' in str(script).lower():
                    platform_scores['amazon'] += 20
            
            # Get the platform with highest score
            max_platform = max(platform_scores.items(), key=lambda x: x[1])
            platform, score = max_platform
            
            # Only return a platform if we're reasonably confident
            if score > 30:
                current_app.logger.info(f"Detected platform {platform} with confidence {score}")
                return {
                    'platform': platform,
                    'confidence': min(score, 100)  # Cap confidence at 100
                }
            
            return {
                'platform': 'unknown',
                'confidence': 0
            }
            
        except Exception as e:
            current_app.logger.error(f"Error detecting platform: {str(e)}")
            return {
                'platform': 'unknown',
                'confidence': 0
            } 