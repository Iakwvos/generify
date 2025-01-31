import requests
from flask import current_app
import json
from datetime import datetime, timedelta
import os

class ShopifyService:
    def __init__(self):
        self.base_url = None
        self.access_token = None
        self.headers = None
    
    def initialize(self, store_url, access_token):
        """Initialize service with store URL and access token"""
        self.base_url = f"https://{store_url}/admin/api/2024-01"
        self.access_token = access_token
        self.headers = {
            'X-Shopify-Access-Token': access_token,
            'Content-Type': 'application/json'
        }

    def _init_config(self):
        """Initialize configuration from Flask config"""
        if not self.base_url or not self.access_token:
            try:
                store_url = current_app.config.get('SHOP_URL')
                access_token = current_app.config.get('ACCESS_TOKEN')
                
                if not store_url or not access_token:
                    raise ValueError("Missing Shopify configuration. Please check SHOP_URL and ACCESS_TOKEN in config.py")
                    
                self.initialize(store_url, access_token)
                
            except RuntimeError as e:
                if "Working outside of application context" in str(e):
                    current_app.logger.error("ShopifyService must be used within Flask application context")
                    raise ValueError("Service must be used within Flask application context") from e
                raise
    
    def get_product(self, product_id):
        """Get a single product by ID
        
        Args:
            product_id (str): The ID of the product to retrieve
            
        Returns:
            dict: Product data
        """
        self._init_config()
        
        try:
            response = requests.get(
                f"{self.base_url}/products/{product_id}.json",
                headers=self.headers
            )
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            return response.json().get('product', {})
            
        except Exception as e:
            current_app.logger.error(f"Error getting product {product_id}: {str(e)}")
            raise ValueError(f"Failed to get product: {str(e)}")
    
    def get_products(self):
        """Fetch all products from Shopify store"""
        self._init_config()
        response = requests.get(
            f"{self.base_url}/products.json",
            headers=self.headers
        )
        products = response.json().get('products', [])
        
        # Process each product to ensure required fields
        for product in products:
            # Ensure required fields have default values
            product['handle'] = product.get('handle', self._generate_handle(product.get('title', 'untitled')))
            product['vendor'] = product.get('vendor', '')
            product['product_type'] = product.get('product_type', '')
            product['status'] = product.get('status', 'active')
            product['tags'] = product.get('tags', '')
            product['template_suffix'] = product.get('template_suffix', '')
            
            # Ensure images have default values
            product['images'] = [
                {
                    'src': img.get('src', ''),
                    'alt': img.get('alt', '')
                }
                for img in product.get('images', [])
            ]
            
            # Ensure variants have required fields
            for variant in product.get('variants', []):
                variant['title'] = variant.get('title', '')
                variant['price'] = float(variant.get('price', 0))
                variant['inventory_quantity'] = int(variant.get('inventory_quantity', 0))
                variant['sku'] = variant.get('sku', '')
                variant['barcode'] = variant.get('barcode', '')
                variant['weight'] = float(variant.get('weight', 0))
                variant['weight_unit'] = variant.get('weight_unit', 'g')
        
        return products
    
    def get_themes(self):
        """Fetch all themes from Shopify store"""
        self._init_config()
        response = requests.get(
            f"{self.base_url}/themes.json",
            headers=self.headers
        )
        return response.json().get('themes', [])
    
    def get_theme_assets(self, theme_id):
        """Fetch all assets for a specific theme"""
        self._init_config()
        response = requests.get(
            f"{self.base_url}/themes/{theme_id}/assets.json",
            headers=self.headers
        )
        return response.json().get('assets', [])

    def create_product(self, title, language='en', price=None, url=None, template_suffix=None, images=None):
        """Create a new product in Shopify store
        
        Args:
            title (str): Product title
            language (str): Language code (default: 'en')
            price (str): Product price
            url (str): Reference URL
            template_suffix (str): Template suffix for the product
            images (list): List of image objects with src, alt, width, height
            
        Returns:
            dict: Created product data
        """
        self._init_config()
        
        try:
            # Validate required fields
            if not title:
                raise ValueError("Product title is required")
            
            current_app.logger.info(f"Creating product '{title}' with {len(images) if images else 0} images")
                
            # Prepare product data
            product_data = {
                "product": {
                    "title": title,
                    "body_html": "<p>Product description coming soon...</p>",
                    "vendor": "",
                    "product_type": "",
                    "status": "active",
                    "template_suffix": template_suffix,
                    "variants": [{
                        "price": str(price) if price else "0.00",
                        "inventory_quantity": 0,
                        "inventory_management": "shopify",
                        "inventory_policy": "continue",
                        "requires_shipping": True,
                        "taxable": True
                    }],
                    "options": [{
                        "name": "Title",
                        "values": ["Default Title"]
                    }],
                    "metafields": [{
                        "namespace": "custom",
                        "key": "language",
                        "value": language,
                        "type": "single_line_text_field"
                    }]
                }
            }

            # Add reference URL if provided
            if url:
                current_app.logger.info(f"Adding reference URL: {url}")
                product_data["product"]["metafields"].append({
                    "namespace": "custom",
                    "key": "reference_url",
                    "value": url,
                    "type": "single_line_text_field"
                })

            # Add images if provided
            if images:
                current_app.logger.info(f"Processing {len(images)} images")
                product_data["product"]["images"] = []
                for idx, img in enumerate(images):
                    try:
                        image_data = {
                            "src": img['src'],
                            "alt": img.get('alt', ''),
                        }
                        if 'width' in img and 'height' in img:
                            image_data["width"] = img['width']
                            image_data["height"] = img['height']
                        product_data["product"]["images"].append(image_data)
                        current_app.logger.info(f"Added image {idx + 1}: {img['src']}")
                    except Exception as img_error:
                        current_app.logger.error(f"Error processing image {idx + 1}: {str(img_error)}")

            # Create the product
            current_app.logger.info("Sending create product request to Shopify")
            response = requests.post(
                f"{self.base_url}/products.json",
                headers=self.headers,
                json=product_data
            )
            
            # Handle response
            if response.status_code == 401:
                current_app.logger.error("Authentication failed with Shopify API")
                raise ValueError("Invalid Shopify access token. Please check your SHOPIFY_ACCESS_TOKEN configuration.")
            elif response.status_code == 404:
                current_app.logger.error("Resource not found at Shopify API")
                raise ValueError("Resource not found")
            elif response.status_code == 422:
                error_data = response.json()
                current_app.logger.error(f"Invalid product data: {error_data}")
                raise ValueError(f"Invalid product data: {error_data.get('errors', response.text)}")
            elif response.status_code != 201:
                current_app.logger.error(f"Unexpected response from Shopify: {response.status_code}")
                raise ValueError(f"Unexpected response from Shopify: {response.status_code}")
            
            response.raise_for_status()
            product = response.json().get('product', {})
            current_app.logger.info(f"Product created successfully with ID: {product.get('id')}")
            return product
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Network error creating product: {str(e)}")
            raise ValueError(f"Failed to create product: {str(e)}")
        except ValueError as e:
            current_app.logger.error(f"Validation error creating product: {str(e)}")
            raise
        except Exception as e:
            current_app.logger.error(f"Unexpected error creating product: {str(e)}")
            raise ValueError(f"Error creating product: {str(e)}")

    def _make_request(self, method, endpoint, data=None, files=None):
        """Make a request to the Shopify API"""
        try:
            self._ensure_initialized()
            
            headers = {
                'X-Shopify-Access-Token': self.access_token,
                'Content-Type': 'application/json'
            }

            url = f"{self.base_url}{endpoint}"
            
            if files:
                del headers['Content-Type']
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=json.dumps(data) if data and not files else data,
                files=files
            )
            
            if response.status_code == 401:
                raise ValueError("Invalid Shopify access token. Please check your SHOPIFY_ACCESS_TOKEN configuration.") from e
            elif response.status_code == 404:
                raise ValueError(f"Resource not found at endpoint: {endpoint}") from e
            elif response.status_code == 422:
                raise ValueError(f"Invalid product data: {response.text}") from e
            
            response.raise_for_status()
            return response.json() if response.content else None
            
        except requests.exceptions.RequestException as e:
            if isinstance(e, requests.exceptions.HTTPError):
                if e.response.status_code == 401:
                    raise ValueError("Authentication failed. Please check your Shopify access token.") from e
                elif e.response.status_code == 429:
                    raise ValueError("Rate limit exceeded. Please try again later.") from e
            raise ValueError(f"Error communicating with Shopify API: {str(e)}") from e 

    def delete_product(self, product_id):
        """Delete a product, its associated template, and all media (images, gifs) from the store
        
        Args:
            product_id (str): The ID of the product to delete
            
        Returns:
            bool: True if deletion was successful
        """
        self._init_config()
        
        try:
            # First get the product to check for template_suffix and media
            product_response = requests.get(
                f"{self.base_url}/products/{product_id}.json",
                headers=self.headers
            )
            product = product_response.json().get('product', {})
            template_suffix = product.get('template_suffix')
            
            # Delete all media (images, gifs) associated with the product
            if 'images' in product:
                current_app.logger.info(f"Deleting {len(product['images'])} media files...")
                for image in product['images']:
                    try:
                        # Delete each image using its ID
                        image_id = image['id']
                        response = requests.delete(
                            f"{self.base_url}/products/{product_id}/images/{image_id}.json",
                            headers=self.headers
                        )
                        if response.status_code == 200:
                            current_app.logger.info(f"Successfully deleted image {image_id}")
                        else:
                            current_app.logger.warning(f"Failed to delete image {image_id}: {response.text}")
                    except Exception as img_error:
                        current_app.logger.error(f"Error deleting image {image_id}: {str(img_error)}")
            
            # If product has a template, delete it
            if template_suffix:
                # Get active theme ID
                themes_response = requests.get(
                    f"{self.base_url}/themes.json",
                    headers=self.headers
                )
                themes = themes_response.json().get('themes', [])
                active_theme = next((theme for theme in themes if theme['role'] == 'main'), None)
                
                if active_theme:
                    # Delete the template asset
                    asset_key = f'templates/product.{template_suffix}.json'
                    template_response = requests.delete(
                        f"{self.base_url}/themes/{active_theme['id']}/assets.json?asset[key]={asset_key}",
                        headers=self.headers
                    )
                    if template_response.status_code == 200:
                        current_app.logger.info(f"Successfully deleted template {asset_key}")
                    else:
                        current_app.logger.warning(f"Failed to delete template {asset_key}: {template_response.text}")
            
            # Finally delete the product
            response = requests.delete(
                f"{self.base_url}/products/{product_id}.json",
                headers=self.headers
            )
            
            success = response.status_code == 200
            if success:
                current_app.logger.info(f"Successfully deleted product {product_id}")
            else:
                current_app.logger.error(f"Failed to delete product {product_id}: {response.text}")
            
            return success
            
        except Exception as e:
            current_app.logger.error(f"Error deleting product: {str(e)}")
            return False

    def duplicate_product(self, product_id):
        """Duplicate an existing product
        
        Args:
            product_id (str): The ID of the product to duplicate
            
        Returns:
            dict: The newly created product data
        """
        self._init_config()
        
        try:
            # Get the original product
            url = f"{self.base_url}/products/{product_id}.json"
            response = requests.get(
                url,
                headers=self.headers
            )
            if response.status_code != 200:
                raise Exception("Failed to get original product")
            
            product_data = response.json()["product"]
            
            # Create new product data with modified title
            new_product = {
                "product": {
                    "title": f"{product_data['title']} (Copy)",
                    "body_html": product_data['body_html'],
                    "vendor": product_data['vendor'],
                    "product_type": product_data['product_type'],
                    "status": product_data['status'],
                    "variants": product_data['variants'],
                    "options": product_data['options'],
                    "tags": product_data.get('tags', ''),
                    "template_suffix": product_data.get('template_suffix'),
                    "images": product_data.get('images', [])
                }
            }
            
            # Create the duplicate
            create_url = f"{self.base_url}/products.json"
            create_response = requests.post(
                create_url,
                headers=self.headers,
                json=new_product
            )
            if create_response.status_code != 201:
                raise Exception("Failed to create duplicate product")
            
            # If original product has a template, duplicate it
            template_suffix = product_data.get('template_suffix')
            if template_suffix:
                try:
                    # Get active theme ID
                    themes_response = requests.get(
                        f"{self.base_url}/themes.json",
                        headers=self.headers
                    )
                    themes = themes_response.json().get('themes', [])
                    active_theme = next((theme for theme in themes if theme['role'] == 'main'), None)
                    
                    if active_theme:
                        # Get original template
                        original_asset_key = f'templates/product.{template_suffix}.json'
                        template_response = requests.get(
                            f"{self.base_url}/themes/{active_theme['id']}/assets.json?asset[key]={original_asset_key}",
                            headers=self.headers
                        )
                        
                        if template_response.status_code == 200:
                            template_data = template_response.json()['asset']['value']
                            
                            # Generate new template suffix
                            import random
                            import string
                            new_suffix = ''.join(random.choices(string.digits, k=10))
                            
                            # Create new template asset
                            new_asset_key = f'templates/product.{new_suffix}.json'
                            asset_data = {
                                'asset': {
                                    'key': new_asset_key,
                                    'value': template_data
                                }
                            }
                            
                            # Create the new template
                            requests.put(
                                f"{self.base_url}/themes/{active_theme['id']}/assets.json",
                                headers=self.headers,
                                json=asset_data
                            )
                            
                            # Update the new product with the new template suffix
                            new_product_id = create_response.json()["product"]["id"]
                            update_response = requests.put(
                                f"{self.base_url}/products/{new_product_id}.json",
                                headers=self.headers,
                                json={
                                    "product": {
                                        "id": new_product_id,
                                        "template_suffix": new_suffix
                                    }
                                }
                            )
                            if update_response.status_code == 200:
                                return update_response.json()["product"]
                except Exception as template_error:
                    current_app.logger.error(f"Error duplicating template: {str(template_error)}")
                    # Continue with the product duplication even if template duplication fails
            
            return create_response.json()["product"]
            
        except Exception as e:
            current_app.logger.error(f"Error duplicating product: {str(e)}")
            raise ValueError(f"Failed to duplicate product: {str(e)}")

    def create_asset(self, key, content):
        """Create an asset in the active theme.
        
        Args:
            key (str): The asset key (path)
            content (dict): The JSON content for the asset
        """
        self._init_config()
        
        try:
            # Get active theme ID
            themes_response = requests.get(
                f"{self.base_url}/themes.json",
                headers=self.headers
            )
            themes = themes_response.json().get('themes', [])
            active_theme = next((theme for theme in themes if theme['role'] == 'main'), None)
            
            if not active_theme:
                raise Exception('No active theme found')
            
            # Create the asset
            asset_data = {
                'asset': {
                    'key': key,
                    'value': json.dumps(content, indent=2, ensure_ascii=False)
                }
            }
            
            response = requests.put(
                f"{self.base_url}/themes/{active_theme['id']}/assets.json",
                headers=self.headers,
                json=asset_data
            )
            
            if response.status_code != 200:
                raise Exception(f'Failed to create asset: {response.text}')
            
            return True
            
        except Exception as e:
            print(f"Error creating asset: {str(e)}")
            raise 

    def update_product(self, product_id, data):
        """Update a product's properties in Shopify store
        
        Args:
            product_id (str): The ID of the product to update
            data (dict): The data to update (e.g., template_suffix)
            
        Returns:
            bool: True if update was successful
        """
        self._init_config()
        
        try:
            current_app.logger.info(f"Updating product {product_id} with data: {json.dumps(data)}")
            
            # Get current product data
            product_response = requests.get(
                f"{self.base_url}/products/{product_id}.json",
                headers=self.headers
            )
            if product_response.status_code != 200:
                raise Exception("Failed to get product data")
            
            current_product = product_response.json()['product']
            
            # Update only the provided fields
            update_data = {
                "product": {
                    **{k: current_product[k] for k in current_product if k != 'admin_graphql_api_id'},
                    **data
                }
            }
            
            # Send update request
            response = requests.put(
                f"{self.base_url}/products/{product_id}.json",
                headers=self.headers,
                json=update_data
            )
            
            if response.status_code != 200:
                current_app.logger.error(f"Failed to update product: {response.text}")
                return False
                
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error updating product: {str(e)}")
            return False 

    def get_analytics_data(self, time_range='30d'):
        """Get analytics data using available scopes (read_analytics, read_products, read_themes)"""
        self._init_config()
        
        # Calculate date range
        end_date = datetime.now()
        if time_range == '7d':
            start_date = end_date - timedelta(days=7)
        elif time_range == '30d':
            start_date = end_date - timedelta(days=30)
        elif time_range == '90d':
            start_date = end_date - timedelta(days=90)
        elif time_range == '1y':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)  # Default to 30 days
            
        try:
            # Get products data
            products = self.get_products()
            themes = self.get_themes()
            
            # Get analytics reports
            reports = self._get_analytics_reports(start_date, end_date)
            
            # Calculate product statistics
            total_products = len(products)
            active_products = len([p for p in products if p.get('status') == 'active'])
            total_variants = sum(len(p.get('variants', [])) for p in products)
            
            # Calculate inventory and pricing metrics
            total_inventory = 0
            total_value = 0
            prices = []
            inventory_by_date = {}
            product_types = {}
            vendors = {}
            
            for product in products:
                # Track product types
                product_type = product.get('product_type', 'Uncategorized')
                if product_type not in product_types:
                    product_types[product_type] = 0
                product_types[product_type] += 1
                
                # Track vendors
                vendor = product.get('vendor', 'Unknown')
                if vendor not in vendors:
                    vendors[vendor] = 0
                vendors[vendor] += 1
                
                for variant in product.get('variants', []):
                    price = float(variant.get('price', 0))
                    inventory = int(variant.get('inventory_quantity', 0))
                    total_inventory += inventory
                    total_value += price * inventory
                    prices.append(price)
                    
                    # Track inventory changes by date
                    updated_at = variant.get('updated_at', '').split('T')[0]
                    if updated_at:
                        if updated_at not in inventory_by_date:
                            inventory_by_date[updated_at] = {'count': 0, 'value': 0}
                        inventory_by_date[updated_at]['count'] += inventory
                        inventory_by_date[updated_at]['value'] += price * inventory
            
            # Calculate price statistics
            avg_price = sum(prices) / len(prices) if prices else 0
            min_price = min(prices) if prices else 0
            max_price = max(prices) if prices else 0
            
            # Get theme statistics
            total_themes = len(themes)
            active_theme = next((theme for theme in themes if theme.get('role') == 'main'), None)
            
            # Prepare daily data for charts
            dates = []
            inventory_data = []
            value_data = []
            
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                dates.append(date_str)
                
                if date_str in inventory_by_date:
                    inventory_data.append(inventory_by_date[date_str]['count'])
                    value_data.append(inventory_by_date[date_str]['value'])
                else:
                    inventory_data.append(0)
                    value_data.append(0)
                
                current_date += timedelta(days=1)
            
            # Calculate top products by inventory value
            top_products = []
            for product in products:
                product_value = 0
                total_units = 0
                views = reports.get('product_views', {}).get(str(product['id']), 0)
                
                for variant in product.get('variants', []):
                    price = float(variant.get('price', 0))
                    inventory = int(variant.get('inventory_quantity', 0))
                    product_value += price * inventory
                    total_units += inventory
                
                top_products.append({
                    'title': product['title'],
                    'inventory': total_units,
                    'value': product_value,
                    'price_range': f"${min(float(v['price']) for v in product['variants']):.2f} - ${max(float(v['price']) for v in product['variants']):.2f}" if len(product['variants']) > 1 else f"${float(product['variants'][0]['price']):.2f}",
                    'views': views,
                    'type': product.get('product_type', 'Uncategorized'),
                    'vendor': product.get('vendor', 'Unknown')
                })
            
            # Sort by value and get top 10
            top_products.sort(key=lambda x: x['value'], reverse=True)
            top_products = top_products[:10]
            
            # Format currency values
            for product in top_products:
                product['value'] = f"{product['value']:.2f}"
            
            # Sort product types and vendors by count
            product_type_data = [{'type': k, 'count': v} for k, v in product_types.items()]
            product_type_data.sort(key=lambda x: x['count'], reverse=True)
            
            vendor_data = [{'name': k, 'count': v} for k, v in vendors.items()]
            vendor_data.sort(key=lambda x: x['count'], reverse=True)
            
            return {
                'total_products': total_products,
                'active_products': active_products,
                'total_variants': total_variants,
                'total_inventory': total_inventory,
                'total_value': f"{total_value:.2f}",
                'avg_price': f"{avg_price:.2f}",
                'min_price': f"{min_price:.2f}",
                'max_price': f"{max_price:.2f}",
                'total_themes': total_themes,
                'active_theme': active_theme.get('name') if active_theme else None,
                'dates': dates,
                'inventory_data': inventory_data,
                'value_data': value_data,
                'top_products': top_products,
                'product_types': product_type_data[:5],  # Top 5 product types
                'vendors': vendor_data[:5],  # Top 5 vendors
                'analytics': {
                    'total_views': reports.get('total_views', 0),
                    'unique_visitors': reports.get('unique_visitors', 0),
                    'avg_session_duration': reports.get('avg_session_duration', 0),
                    'bounce_rate': reports.get('bounce_rate', 0),
                    'top_referrers': reports.get('top_referrers', [])[:5],  # Top 5 referrers
                    'device_breakdown': reports.get('device_breakdown', {})
                },
                # Calculate trends
                'product_trend': self._calculate_trend(total_products, total_products - len([p for p in products if p.get('created_at', '').startswith(dates[0])])),
                'inventory_trend': self._calculate_trend(total_inventory, sum(inventory_data[:len(dates)//2]) / (len(dates)//2)),
                'value_trend': self._calculate_trend(total_value, sum(value_data[:len(dates)//2]) / (len(dates)//2))
            }
            
        except Exception as e:
            current_app.logger.error(f"Error fetching analytics data: {str(e)}")
            raise
            
    def _get_analytics_reports(self, start_date, end_date):
        """Fetch analytics reports from Shopify Analytics API"""
        try:
            # Format dates for API
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            # Get analytics reports
            response = requests.get(
                f"{self.base_url}/reports.json",
                headers=self.headers,
                params={
                    'since': start_date_str,
                    'until': end_date_str,
                    'fields': 'views,visitors,sessions,bounce_rate,referrers,devices'
                }
            )
            response.raise_for_status()
            reports_data = response.json()
            
            # Process reports data
            reports = {
                'total_views': 0,
                'unique_visitors': 0,
                'avg_session_duration': 0,
                'bounce_rate': 0,
                'top_referrers': [],
                'device_breakdown': {},
                'product_views': {}
            }
            
            if 'reports' in reports_data:
                for report in reports_data['reports']:
                    if report.get('name') == 'visits':
                        reports['total_views'] = report.get('data', {}).get('total_views', 0)
                        reports['unique_visitors'] = report.get('data', {}).get('unique_visitors', 0)
                        reports['avg_session_duration'] = report.get('data', {}).get('avg_session_duration', 0)
                        reports['bounce_rate'] = report.get('data', {}).get('bounce_rate', 0)
                    elif report.get('name') == 'referrers':
                        reports['top_referrers'] = report.get('data', [])
                    elif report.get('name') == 'devices':
                        reports['device_breakdown'] = report.get('data', {})
                    elif report.get('name') == 'product_views':
                        reports['product_views'] = report.get('data', {})
            
            return reports
            
        except Exception as e:
            current_app.logger.error(f"Error fetching analytics reports: {str(e)}")
            return {}
    
    def get_orders(self, start_date=None, end_date=None, status='any'):
        """Fetch orders from Shopify store with optional date filtering"""
        self._init_config()
        
        params = {
            'status': status,
            'limit': 250  # Maximum allowed by Shopify
        }
        
        if start_date:
            params['created_at_min'] = f"{start_date}T00:00:00Z"
        if end_date:
            params['created_at_max'] = f"{end_date}T23:59:59Z"
            
        try:
            response = requests.get(
                f"{self.base_url}/orders.json",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json().get('orders', [])
        except Exception as e:
            current_app.logger.error(f"Error fetching orders: {str(e)}")
            raise
    
    def _calculate_period_metrics(self, orders):
        """Calculate basic metrics for a set of orders"""
        total_orders = len(orders)
        total_sales = sum(float(order['total_price']) for order in orders)
        avg_order_value = total_sales / total_orders if total_orders > 0 else 0
        
        return {
            'total_orders': total_orders,
            'total_sales': total_sales,
            'avg_order_value': avg_order_value
        }
    
    def _calculate_trend(self, current_value, previous_value):
        """Calculate percentage trend between two values"""
        if previous_value == 0:
            return 0
        return ((current_value - previous_value) / previous_value) * 100
    
    def _calculate_top_products(self, orders):
        """Calculate top-performing products from orders"""
        product_stats = {}
        
        for order in orders:
            for item in order['line_items']:
                product_id = item['product_id']
                if product_id not in product_stats:
                    product_stats[product_id] = {
                        'title': item['title'],
                        'orders': 0,
                        'revenue': 0,
                        'units_sold': 0
                    }
                
                product_stats[product_id]['orders'] += 1
                product_stats[product_id]['revenue'] += float(item['price']) * item['quantity']
                product_stats[product_id]['units_sold'] += item['quantity']
        
        # Convert to list and sort by revenue
        top_products = list(product_stats.values())
        top_products.sort(key=lambda x: x['revenue'], reverse=True)
        
        # Add conversion rate (placeholder as we don't have view data)
        for product in top_products:
            product['conversion_rate'] = 0  # Requires additional data from Shopify Analytics API
        
        return top_products[:10]  # Return top 10 products 

    def _generate_handle(self, title):
        """Generate a URL-friendly handle from a title
        
        Args:
            title (str): Product title
            
        Returns:
            str: URL-friendly handle
        """
        # Convert to lowercase and replace spaces with hyphens
        handle = title.lower().replace(' ', '-')
        
        # Remove special characters
        handle = ''.join(c for c in handle if c.isalnum() or c == '-')
        
        # Remove multiple consecutive hyphens
        while '--' in handle:
            handle = handle.replace('--', '-')
        
        # Remove leading/trailing hyphens
        handle = handle.strip('-')
        
        # If empty, return a default
        return handle if handle else 'untitled-product' 