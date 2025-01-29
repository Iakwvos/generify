import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin
import random
import time
from fake_useragent import UserAgent
import http.cookiejar
import cloudscraper
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import platform
import threading
from flask import current_app
import gzip
import google.generativeai as genai
import os
import json
from datetime import datetime
import pytz

# Thread-local storage for browser instances
thread_local = threading.local()

class ContentService:
    def __init__(self):
        self.browser_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': f'"{platform.system()}"',
        }
        
        self.referrers = [
            'https://www.google.com/search?q=',
            'https://www.bing.com/search?q=',
            'https://www.facebook.com/',
            'https://t.co/',
            'https://www.instagram.com/',
            'https://www.pinterest.com/',
            'https://www.reddit.com/',
            'https://duckduckgo.com/?q=',
        ]
        
        # Initialize AI model
        self.model = None
        self.initialize_ai()

    def initialize_ai(self):
        """Initialize Gemini configuration within Flask context"""
        try:
            if not self.model:
                api_key = current_app.config.get('GEMINI_API_KEY')
                if not api_key:
                    raise ValueError("GEMINI_API_KEY not found in configuration")
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash-8b')
                current_app.logger.info("Gemini service initialized successfully")
        except Exception as e:
            current_app.logger.error(f"Failed to initialize Gemini service: {str(e)}")
            raise

    def get_local_browser(self):
        """Get or create thread-local browser instance"""
        if not hasattr(thread_local, "browser"):
            options = uc.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            thread_local.browser = uc.Chrome(options=options)
        return thread_local.browser

    def get_enhanced_headers(self, url):
        """Generate enhanced browser-like headers"""
        ua = UserAgent()
        headers = self.browser_headers.copy()
        
        user_agent = ua.random
        headers['User-Agent'] = user_agent
        
        domain = urlparse(url).netloc
        search_query = domain.replace('.', ' ')
        referer = random.choice(self.referrers)
        if '?q=' in referer:
            referer += search_query
        headers['Referer'] = referer
        
        headers['Host'] = urlparse(url).netloc
        
        languages = ['en-US,en;q=0.9', 'en-GB,en;q=0.8', 'en;q=0.7']
        headers['Accept-Language'] = random.choice(languages)
        
        viewports = ['1920x1080', '1366x768', '1536x864', '1440x900', '1280x720']
        viewport = random.choice(viewports)
        headers['Viewport-Width'] = viewport.split('x')[0]
        
        return headers

    def create_enhanced_session(self):
        """Create a session with advanced browser emulation"""
        session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        session.cookies = http.cookiejar.CookieJar()
        return session

    def fetch_with_advanced_retry(self, url, max_retries=3):
        """Enhanced fetch with multiple fallback methods"""
        exceptions = []
        
        try:
            session = self.create_enhanced_session()
            headers = self.get_enhanced_headers(url)
            headers['Accept-Encoding'] = 'gzip, deflate'
            session.headers.update(headers)
            
            time.sleep(random.uniform(2, 5))
            
            response = session.get(url, timeout=30)
            response.raise_for_status()
            
            if response.headers.get('content-encoding') == 'gzip':
                try:
                    return response.text
                except Exception:
                    try:
                        content = gzip.decompress(response.content)
                        return content.decode('utf-8', errors='replace')
                    except Exception as gz_e:
                        current_app.logger.error(f"Gzip decompression failed: {gz_e}")
                        return response.content.decode('utf-8', errors='replace')
            
            return response.text
            
        except Exception as e:
            exceptions.append(f"Cloudscraper attempt failed: {str(e)}")
        
        try:
            browser = self.get_local_browser()
            browser.get(url)
            
            WebDriverWait(browser, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            return browser.page_source
        except Exception as e:
            exceptions.append(f"Selenium attempt failed: {str(e)}")
            raise Exception(f"All fetch methods failed: {'; '.join(exceptions)}")

    def clean_html(self, html_content):
        """Clean and process HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            images = []
            for img in soup.find_all('img'):
                src = img.get('src', '')
                alt = img.get('alt', '')
                width = img.get('width', '')
                height = img.get('height', '')
                class_name = img.get('class', [])
                if isinstance(class_name, list):
                    class_name = ' '.join(class_name)
                
                if src:
                    images.append({
                        'src': src,
                        'alt': alt,
                        'width': width,
                        'height': height,
                        'class': class_name
                    })

            for element in soup.find_all(['script', 'style']):
                element.decompose()

            cleaned_content = []
            
            for element in soup.descendants:
                if isinstance(element, str) and element.strip():
                    cleaned_content.append(element.strip())
                elif element.name == 'img':
                    try:
                        new_img = soup.new_tag('img')
                        essential_attrs = ['src', 'alt', 'title', 'width', 'height']
                        for attr in essential_attrs:
                            if element.get(attr):
                                new_img[attr] = element[attr]
                        cleaned_content.append(str(new_img))
                    except AttributeError:
                        continue
            
            cleaned_html = '\n'.join(line for line in cleaned_content if line)
            
            return cleaned_html, images
            
        except Exception as e:
            raise Exception(f"Error cleaning HTML: {str(e)}")

    def analyze_content(self, url, cleaned_content, images, language):
        """Analyze content and generate AI responses"""
        if not self.model:
            raise Exception("Gemini AI not configured. Please set GEMINI_API_KEY environment variable.")

        # Create image analysis prompt
        image_prompt = f"""Analyze these images and determine which ones are likely product images.
Consider:
1. Image dimensions (product images are usually square or landscape)
2. Alt text (look for product-related descriptions)
3. Class names (look for product-related classes)
4. URL patterns (look for product-related paths)

Return a JSON array with maximum 5 most likely product image URLs.

Images to analyze:
{json.dumps(images, indent=2)}

Response format:
["url1", "url2", ...]"""

        # Get product images
        image_response = self.model.generate_content(image_prompt)
        try:
            product_images = json.loads(image_response.text.replace("```json", "").replace("```", "").strip())
            if not isinstance(product_images, list):
                product_images = []
            product_images = product_images[:5]  # Ensure max 5 images
        except:
            product_images = []

        # Platform detection prompt
        platform_prompt = f"""Analyze this HTML content and determine which e-commerce platform it's from (Shopify, WordPress, etc.).
Return a JSON object with:
1. platform_name: detected platform
2. confidence_score: 0-100
3. explanation: why you think it's this platform (max 15 words)
4. IMPORTANT: Generate ALL content in the specified language ({language}).

HTML Content:
{cleaned_content}"""

        # Detect platform
        platform_response = self.model.generate_content(platform_prompt)
        platform_content = platform_response.text.replace("```json", "").replace("```", "").strip()
        platform_info = json.loads(platform_content)

        # Main content generation prompt
        json_template = {
            "Product Title": "ExampleProduct™",
            "sections.main.blocks.reviews_number_wmFXyt.settings.reviews_text": "437 reviews"
        }

        # Build prompt in parts
        prompt_parts = [
            "Analyze the following HTML content and generate product information in JSON format.",
            "The response should be a valid JSON object where each key corresponds to the section name and each value follows the instruction in brackets."
            "Do not include the instruction text in brackets in the output, generate actual content instead.",
            f"IMPORTANT: Generate ALL content in the specified language ({language})",
            "",
            "HTML Content to analyze:",
            cleaned_content,
            "",
            "Instructions for each section:",
            json.dumps([
                ("Product Title", "[Create a short, brand sounding title with ™]"),
                ("sections.main.blocks.reviews_number_wmFXyt.settings.reviews_text", "[x reviews, usually randomly between 300-700]"),
                ("sections.main.blocks.pp_text_VLf9ic.settings.pp_text", "[Summarize the product features and benefits based on the URL content. Aim for 40-50 words.]"),
                ("sections.main.blocks.pp_benefits_Lfapdf.settings.pp_benefits_text1", "[Key features in bullet point, 10-15 words, starting with a ✔️]"),
                ("sections.main.blocks.pp_benefits_Lfapdf.settings.pp_benefits_text2", "[Key features in bullet point, 10-15 words, starting with a ✔️]"),
                ("sections.main.blocks.pp_benefits_Lfapdf.settings.pp_benefits_text3", "[Key features in bullet point, 10-15 words, starting with a ✔️]"),
                ("sections.main.blocks.pp_benefits_Lfapdf.settings.pp_benefits_text4", "[Key features in bullet point, 10-15 words, starting with a ✔️]"),
                ("sections.main.blocks.pp_review_DzipVt.settings.pp_review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
                ("sections.main.blocks.pp_review_DzipVt.settings.pp_review_author_badge_text", "[random full name, from context decide of gender]"),
                ("sections.pp_image_with_benefits_gkXTTj.settings.heading", "[A catchy hook, 5-8 words.]"),
                ("sections.pp_image_with_benefits_gkXTTj.settings.text", "[Provide a brief overview of how the product based on the catchy hook provided before. Aim for 40-50 words.]"),
                ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_7CB6Bn.settings.text", "[key benefit, 8-12 words]"),
                ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_7CB6Bn.settings.heading", "[One word summarizing sections.pp_image_with_benefits_gkXTTj.blocks.benefit_7CB6Bn.settings.text]"),
                ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_7CB6Bn.settings.emoji", "[One emoji summarizing sections.pp_image_with_benefits_gkXTTj.blocks.benefit_7CB6Bn.settings.text]"),
                ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_7HpQgA.settings.text", "[key benefit, 8-12 words]"),
                ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_7HpQgA.settings.heading", "[One word summarizing sections.pp_image_with_benefits_gkXTTj.blocks.benefit_7HpQgA.settings.text]"),
                ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_7HpQgA.settings.emoji", "[One emoji summarizing sections.pp_image_with_benefits_gkXTTj.blocks.benefit_7HpQgA.settings.text]"),
                ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_erNb6q.settings.text", "[key benefit, 8-12 words]"),
                ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_erNb6q.settings.heading", "[One word summarizing sections.pp_image_with_benefits_gkXTTj.blocks.benefit_erNb6q.settings.text]"),
                ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_erNb6q.settings.emoji", "[One emoji summarizing sections.pp_image_with_benefits_gkXTTj.blocks.benefit_erNb6q.settings.text]"),
                ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_gJWaeR.settings.text", "[key benefit, 8-12 words]"),
                ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_gJWaeR.settings.heading", "[One word summarizing sections.pp_image_with_benefits_gkXTTj.blocks.benefit_gJWaeR.settings.text]"),
                ("sections.pp_image_with_benefits_gkXTTj.blocks.benefit_gJWaeR.settings.emoji", "[One emoji summarizing sections.pp_image_with_benefits_gkXTTj.blocks.benefit_gJWaeR.settings.text]"),
                ("sections.pp_image_with_text_BVEaDq.blocks.heading_aFxCRe.settings.heading", "[A text explaining how the product enhances your life in 10-15 words.]"),
                ("sections.pp_image_with_text_BVEaDq.blocks.text_ifpgzE.settings.text", "[Describe the heading from sections.pp_image_with_text_BVEaDq.blocks.heading_aFxCRe.settings.heading. Aim for 40-50 words.]"),
                ("sections.pp_image_with_percentage_fLf47C.blocks.heading_UYwMbc.settings.heading", "[text in style \"Why choose x product?\"]"),
                ("sections.pp_image_with_percentage_fLf47C.blocks.percent_MDgdzN.settings.text", "[first reason why this product is better, 3-5 words.]"),
                ("sections.pp_image_with_percentage_fLf47C.blocks.percent_MDgdzN.settings.percent_value", "[random number between 88-98, saved as integer]"),
                ("sections.pp_image_with_percentage_fLf47C.blocks.percent_DNwFD7.settings.text", "[second reason why this product is better, 3-5 words.]"),
                ("sections.pp_image_with_percentage_fLf47C.blocks.percent_DNwFD7.settings.percent_value", "[random number between 88-98, saved as integer]"),
                ("sections.pp_image_with_percentage_fLf47C.blocks.percent_Wh6UWW.settings.text", "[third reason why this product is better, 3-5 words.]"),
                ("sections.pp_image_with_percentage_fLf47C.blocks.percent_Wh6UWW.settings.percent_value", "[random number between 88-98, saved as integer]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_UYYj4E.settings.author_text", "[random full name, from context decide of gender]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_UYYj4E.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_V7CyvK.settings.author_text", "[random full name, from context decide of gender]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_V7CyvK.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_Z0kjRL.settings.author_text", "[random full name, from context decide of gender]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_Z0kjRL.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_pt5PN0.settings.author_text", "[random full name, from context decide of gender]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_pt5PN0.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_UayexO.settings.author_text", "[random full name, from context decide of gender]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_UayexO.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_pcN8mI.settings.author_text", "[random full name, from context decide of gender]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_pcN8mI.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_FRVTX7.settings.author_text", "[random full name, from context decide of gender]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_FRVTX7.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_AUSNsH.settings.author_text", "[random full name, from context decide of gender]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_AUSNsH.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_gbJSSq.settings.author_text", "[random full name, from context decide of gender]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_gbJSSq.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_325MmR.settings.author_text", "[random full name, from context decide of gender]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_325MmR.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_SqYPOw.settings.author_text", "[random full name, from context decide of gender]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_SqYPOw.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_nJQgxL.settings.author_text", "[random full name, from context decide of gender]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_nJQgxL.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_6WimSV.settings.author_text", "[random full name, from context decide of gender]"),
                ("sections.pp_reviews_dqQHmw.blocks.review_6WimSV.settings.review_text", "[Create a hypothetical customer review highlighting the product's benefits. Aim for 30-40 words.]"),
                ("sections.pp_comparison_table_ttamEN.blocks.heading_Wjx9pp.settings.heading", "[heading in format \"Why x product and not it's competitor?\"]"),
                ("sections.pp_comparison_table_ttamEN.blocks.text_4ad9ba.settings.text", "[Explanation on why it's better than anything else in the market, 50-70 words]"),
                ("sections.pp_comparison_table_ttamEN.blocks.tableitem_6hMT9z.settings.text", "[1 word of main trait of the product]"),
                ("sections.pp_comparison_table_ttamEN.blocks.tableitem_KNWAfa.settings.text", "[1 word of main trait of the product]"),
                ("sections.pp_comparison_table_ttamEN.blocks.tableitem_jB68ak.settings.text", "[1 word of main trait of the product]"),
                ("sections.pp_comparison_table_ttamEN.blocks.tableitem_CVBp68.settings.text", "[1 word of main trait of the product]"),
                ("sections.pp_comparison_table_ttamEN.blocks.tableitem_6Crhhq.settings.text", "[1 word of main trait of the product]"),
                ("sections.pp_faq_TtURdM.blocks.question_UUEbPG.settings.heading", "[Question regarding this product, 10-15 words]"),
                ("sections.pp_faq_TtURdM.blocks.question_UUEbPG.settings.text", "[Answer to question sections.pp_faq_TtURdM.blocks.question_UUEbPG.settings.text]"),
                ("sections.pp_faq_TtURdM.blocks.question_iwgzRn.settings.heading", "[Question regarding this product, 10-15 words]"),
                ("sections.pp_faq_TtURdM.blocks.question_iwgzRn.settings.text", "[Answer to question sections.pp_faq_TtURdM.blocks.question_iwgzRn.settings.text]"),
                ("sections.pp_faq_TtURdM.blocks.question_gNmdPq.settings.heading", "[Question regarding this product, 10-15 words]"),
                ("sections.pp_faq_TtURdM.blocks.question_gNmdPq.settings.text", "[Answer to question sections.pp_faq_TtURdM.blocks.question_gNmdPq.settings.text]"),
                ("sections.pp_faq_TtURdM.blocks.question_NpRfRa.settings.heading", "[Question regarding this product, 10-15 words]"),
                ("sections.pp_faq_TtURdM.blocks.question_NpRfRa.settings.text", "[Answer to question sections.pp_faq_TtURdM.blocks.question_NpRfRa.settings.text]"),
                ("sections.pp_faq_TtURdM.blocks.question_cwFiY9.settings.heading", "[Question regarding this product, 10-15 words]"),
                ("sections.pp_faq_TtURdM.blocks.question_cwFiY9.settings.text", "[Answer to question sections.pp_faq_TtURdM.blocks.question_cwFiY9.settings.text]")
            ], indent=2),
            "",
            "Important:",
            "1. Generate actual content, not the instructions in brackets",
            "2. Ensure the response is valid JSON",
            "3. Use the exact section names as keys",
            "4. Make the content engaging and marketing-focused",
            "5. Maintain consistent tone throughout",
            f"6. IMPORTANT: ALL content must be in {language} language",
            "",
            "Response format example:",
            json.dumps(json_template, indent=2)
        ]

        # Join all parts with newlines
        main_prompt = "\n".join(prompt_parts)

        # Generate main content
        main_response = self.model.generate_content(main_prompt)
        main_content = main_response.text.replace("```json", "").replace("```", "").strip()
        
        try:
            result = json.loads(main_content)
        except json.JSONDecodeError:
            # Try to extract JSON if it's wrapped in other text
            start_idx = main_content.find("{")
            end_idx = main_content.rfind("}")
            if start_idx != -1 and end_idx != -1:
                json_str = main_content[start_idx:end_idx + 1]
                result = json.loads(json_str)
            else:
                raise ValueError("Could not extract valid JSON from response")

        # Calculate token usage and pricing
        total_input_tokens = len(main_prompt.split()) + len(image_prompt.split()) + len(platform_prompt.split())
        total_output_tokens = len(main_response.text.split()) + len(image_response.text.split()) + len(platform_response.text.split())
        
        # Calculate pricing
        input_price = (total_input_tokens / 1_000_000) * 0.0375  # $0.0375 per 1M tokens
        output_price = (total_output_tokens / 1_000_000) * 0.15   # $0.15 per 1M tokens
        cache_price = (total_input_tokens / 1_000_000) * 0.01    # $0.01 per 1M tokens
        total_price = input_price + output_price + cache_price

        return {
            'platform_detection': platform_info,
            'product_images': product_images,
            'content': result,
            'token_usage': {
                'input_tokens': total_input_tokens,
                'output_tokens': total_output_tokens,
                'pricing': {
                    'input_cost': round(input_price, 6),
                    'output_cost': round(output_price, 6),
                    'cache_cost': round(cache_price, 6),
                    'total_cost': round(total_price, 6)
                }
            }
        } 