from flask import Blueprint, jsonify, request, current_app
from services.shopify_service import ShopifyService
from services.gemini_service import GeminiService
from services.image_service import ImageService
from services.platform_service import PlatformService
from services.content_service import ContentService
import google.generativeai as genai
import os
import json
import random
import string
from flask_restx import Api, Resource, fields, Namespace
from flask import session
from datetime import datetime
import time

# Create blueprint first
api_bp = Blueprint('api', __name__)

# Initialize API with enhanced documentation
api = Api(
    api_bp,
    version='1.0',
    title='Generify API',
    description='''
    Welcome to the Generify API! This API provides endpoints for managing your Shopify store, including:
    
    * Product management
    * Theme customization
    * AI-powered content generation
    * Image processing and optimization
    * Store analytics and insights
    
    For authentication, use your API key in the X-API-KEY header.
    ''',
    doc='/docs',
    authorizations={
        'apikey': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-API-KEY',
            'description': 'API Key for authentication'
        }
    },
    security='apikey',
    default='Products',  # Default namespace to show
    default_label='Generify API Endpoints',
    validate=True,  # Enable payload validation
    ordered=True,  # Keep endpoints ordered as defined
)

# Create namespaces with enhanced descriptions
products_ns = Namespace(
    'products', 
    description='Product management endpoints for creating, updating, and managing Shopify products'
)
themes_ns = Namespace(
    'themes', 
    description='Theme management endpoints for customizing your store appearance'
)
ai_ns = Namespace(
    'ai', 
    description='AI-powered features for content generation and store optimization'
)
images_ns = Namespace(
    'images', 
    description='Image processing endpoints for optimization and extraction'
)
templates_ns = Namespace(
    'templates', 
    description='Template management for custom product pages'
)
store_ns = Namespace(
    'store', 
    description='Store management endpoints for configuration and settings'
)

# Register namespaces
api.add_namespace(products_ns)
api.add_namespace(themes_ns)
api.add_namespace(ai_ns)
api.add_namespace(images_ns)
api.add_namespace(templates_ns)
api.add_namespace(store_ns)

# Create analytics namespace
analytics_ns = Namespace(
    'analytics',
    description='Analytics endpoints for store insights and performance metrics'
)
api.add_namespace(analytics_ns)

# Analytics models
analytics_time_range = analytics_ns.model('TimeRange', {
    'time_range': fields.String(
        description='Time range for analytics',
        enum=['7d', '30d', '90d', '1y'],
        default='30d'
    )
})

product_analytics = analytics_ns.model('ProductAnalytics', {
    'summary': fields.Raw(description='Summary of product metrics'),
    'product_types': fields.List(fields.Raw, description='Product type distribution'),
    'vendors': fields.List(fields.Raw, description='Vendor distribution'),
    'price_distribution': fields.List(fields.Raw, description='Price range distribution')
})

order_analytics = analytics_ns.model('OrderAnalytics', {
    'summary': fields.Raw(description='Summary of order metrics'),
    'daily_metrics': fields.List(fields.Raw, description='Daily order metrics')
})

theme_analytics = analytics_ns.model('ThemeAnalytics', {
    'summary': fields.Raw(description='Summary of theme metrics'),
    'theme_statuses': fields.List(fields.Raw, description='Theme status distribution'),
    'themes': fields.List(fields.Raw, description='Detailed theme information')
})

store_performance = analytics_ns.model('StorePerformance', {
    'traffic': fields.Raw(description='Traffic metrics'),
    'top_referrers': fields.List(fields.Raw, description='Top traffic referrers'),
    'device_breakdown': fields.Raw(description='Device usage breakdown')
})

dashboard_summary = analytics_ns.model('DashboardSummary', {
    'products': fields.Raw(description='Product metrics summary'),
    'orders': fields.Raw(description='Order metrics summary'),
    'themes': fields.Raw(description='Theme metrics summary'),
    'performance': fields.Raw(description='Performance metrics summary'),
    'time_range': fields.String(description='Time range of the analytics')
})

def get_shopify_service():
    """Get or create ShopifyService instance"""
    if not hasattr(current_app, 'shopify_service'):
        current_app.shopify_service = ShopifyService()
    return current_app.shopify_service

def get_analytics_service():
    """Get or create AnalyticsService instance"""
    if not hasattr(current_app, 'analytics_service'):
        from services.analytics_service import AnalyticsService
        current_app.analytics_service = AnalyticsService()
    return current_app.analytics_service

# Enhanced error models
error_response = api.model('ErrorResponse', {
    'message': fields.String(required=True, description='Error message'),
    'error_code': fields.String(description='Internal error code for tracking'),
    'details': fields.Raw(description='Additional error details')
})

# Enhanced product models with examples and descriptions
product_variant = api.model('ProductVariant', {
    'id': fields.String(required=True, description='Unique variant ID', example='gid://shopify/ProductVariant/123'),
    'title': fields.String(required=True, description='Variant title (e.g., "Small / Red")', example='Small / Red'),
    'price': fields.Float(required=True, description='Variant price in store currency', example=29.99),
    'inventory_quantity': fields.Integer(required=True, description='Available quantity in stock', example=100),
    'sku': fields.String(description='Stock Keeping Unit', example='SMR-123'),
    'barcode': fields.String(description='Product barcode (ISBN, UPC, GTIN, etc.)', example='123456789'),
    'weight': fields.Float(description='Weight in grams', example=200),
    'weight_unit': fields.String(description='Weight unit (g, kg, oz, lb)', example='g')
})

product = api.model('Product', {
    'id': fields.String(description='Unique product ID', example='gid://shopify/Product/123'),
    'title': fields.String(required=True, description='Product title', example='Premium T-Shirt'),
    'description': fields.String(description='Product description in HTML', example='<p>High-quality cotton t-shirt...</p>'),
    'price': fields.Float(required=True, description='Base product price', example=29.99),
    'variants': fields.List(fields.Nested(product_variant), description='Product variants'),
    'vendor': fields.String(description='Product vendor/brand', example='Nike', default=''),
    'product_type': fields.String(description='Product type/category', example='Apparel', default=''),
    'status': fields.String(description='Product status', enum=['active', 'draft', 'archived'], example='active', default='active'),
    'tags': fields.String(description='Product tags as comma-separated string', example='summer,new-arrival', default=''),
    'template_suffix': fields.String(description='Product template suffix', example='custom-template', default=''),
    'images': fields.List(fields.Nested(api.model('ProductImage', {
        'src': fields.String(description='Image URL'),
        'alt': fields.String(description='Image alt text', default='')
    })), description='Product images', default=[])
})

theme = api.model('Theme', {
    'id': fields.String(required=True, description='Theme ID'),
    'name': fields.String(required=True, description='Theme name'),
    'role': fields.String(description='Theme role'),
    'created_at': fields.DateTime(description='Creation timestamp')
})

asset = api.model('Asset', {
    'key': fields.String(required=True, description='Asset key'),
    'public_url': fields.String(required=True, description='Public URL'),
    'size': fields.Integer(description='File size in bytes'),
    'content_type': fields.String(description='MIME type')
})

# Store connection models
store_connection_request = api.model('StoreConnectionRequest', {
    'store_url': fields.String(required=True, description='Shopify store URL (e.g., your-store.myshopify.com)'),
    'api_key': fields.String(required=True, description='Admin API access token')
})

store_connection_response = api.model('StoreConnectionResponse', {
    'message': fields.String(description='Success or error message'),
    'store_url': fields.String(description='Connected store URL')
})

# Product endpoints
@products_ns.route('/')
class ProductList(Resource):
    @products_ns.doc(
        description='List all products in your Shopify store',
        responses={
            200: ('Successfully retrieved products', product),
            401: ('Unauthorized - Invalid or missing API key', error_response),
            500: ('Internal server error', error_response)
        }
    )
    @products_ns.marshal_list_with(product)
    def get(self):
        """List all products"""
        try:
            return get_shopify_service().get_products()
        except Exception as e:
            api.abort(500, str(e), error_code='PRODUCT_LIST_ERROR')

    @products_ns.doc(
        description='Create a new product in your Shopify store',
        responses={
            201: ('Product created successfully', product),
            400: ('Invalid request data', error_response),
            401: ('Unauthorized - Invalid or missing API key', error_response),
            500: ('Internal server error', error_response)
        }
    )
    @products_ns.expect(product)
    @products_ns.response(201, 'Product created successfully')
    def post(self):
        """Create a new product"""
        try:
            data = api.payload
            shopify_service = get_shopify_service()
            
            # Extract required fields
            title = data.get('title')
            if not title:
                api.abort(400, "Product title is required", error_code='MISSING_TITLE')
                
            price = data.get('price', '0.00')
            language = data.get('language', 'en')
            url = data.get('url')
            template_suffix = data.get('template_suffix')
            images = data.get('images', [])
            
            # Log the creation attempt
            current_app.logger.info(f"Creating product with title: {title}")
            current_app.logger.info(f"Number of images: {len(images)}")
            
            # Create the product
            product = shopify_service.create_product(
                title=title,
                language=language,
                price=price,
                url=url,
                template_suffix=template_suffix,
                images=images
            )
            
            # Get the full product data to ensure all fields are present
            if product and product.get('id'):
                product = shopify_service.get_product(product['id'])
            
            current_app.logger.info(f"Product created successfully with ID: {product.get('id')}")
            return product, 201
            
        except ValueError as e:
            current_app.logger.error(f"Invalid product data: {str(e)}")
            api.abort(400, str(e), error_code='INVALID_PRODUCT_DATA')
        except Exception as e:
            current_app.logger.error(f"Error creating product: {str(e)}")
            api.abort(500, str(e), error_code='PRODUCT_CREATE_ERROR')

@products_ns.route('/<id>')
@products_ns.param('id', 'Product identifier (Shopify GID)')
class Product(Resource):
    @products_ns.doc(
        description='Update an existing product',
        responses={
            200: ('Product updated successfully', product),
            400: ('Invalid request data', error_response),
            401: ('Unauthorized - Invalid or missing API key', error_response),
            404: ('Product not found', error_response),
            500: ('Internal server error', error_response)
        }
    )
    @products_ns.expect(product)
    @products_ns.response(200, 'Product updated successfully')
    def put(self, id):
        """
        Update a product
        
        Updates an existing product with the provided details. You can update any product
        attribute including variants, images, and metadata.
        """
        try:
            return get_shopify_service().update_product(id, api.payload)
        except ValueError as e:
            api.abort(400, str(e), error_code='INVALID_PRODUCT_DATA')
        except Exception as e:
            api.abort(500, str(e), error_code='PRODUCT_UPDATE_ERROR')

    @products_ns.doc(
        description='Partially update a product',
        responses={
            200: ('Product updated successfully', product),
            400: ('Invalid request data', error_response),
            401: ('Unauthorized - Invalid or missing API key', error_response),
            404: ('Product not found', error_response),
            500: ('Internal server error', error_response)
        }
    )
    @products_ns.expect(api.model('ProductPatch', {
        'template_suffix': fields.String(description='Product template suffix', example='custom-template')
    }))
    @products_ns.response(200, 'Product updated successfully')
    def patch(self, id):
        """
        Partially update a product
        
        Updates specific fields of an existing product. Currently supports updating template_suffix.
        """
        try:
            data = api.payload
            if 'template_suffix' not in data:
                api.abort(400, "Only template_suffix updates are supported", error_code='INVALID_UPDATE')
                
            return get_shopify_service().update_product(id, {'template_suffix': data['template_suffix']})
        except ValueError as e:
            api.abort(400, str(e), error_code='INVALID_PRODUCT_DATA')
        except Exception as e:
            api.abort(500, str(e), error_code='PRODUCT_UPDATE_ERROR')

    @products_ns.doc(
        description='Delete a product',
        responses={
            204: 'Product deleted successfully',
            401: ('Unauthorized - Invalid or missing API key', error_response),
            404: ('Product not found', error_response),
            500: ('Internal server error', error_response)
        }
    )
    @products_ns.response(204, 'Product deleted')
    def delete(self, id):
        """
        Delete a product
        
        Permanently deletes a product and all its variants, images, and associated assets from your Shopify store.
        This action cannot be undone.
        """
        try:
            shopify_service = get_shopify_service()
            
            # Get product data before deletion to access template and images
            product = shopify_service.get_product(id)
            if not product:
                api.abort(404, "Product not found", error_code='PRODUCT_NOT_FOUND')
            
            # Store template suffix and image URLs
            template_suffix = product.get('template_suffix')
            images = product.get('images', [])
            
            # Delete the product first
            shopify_service.delete_product(id)
            
            # Delete the template asset if it exists
            if template_suffix:
                try:
                    asset_key = f'templates/product.{template_suffix}.json'
                    shopify_service.delete_asset(asset_key)
                    current_app.logger.info(f"Deleted template asset: {asset_key}")
                except Exception as e:
                    current_app.logger.warning(f"Failed to delete template asset: {str(e)}")
            
            # Delete all associated images
            for image in images:
                try:
                    if image.get('src'):
                        shopify_service.delete_image(image['src'])
                        current_app.logger.info(f"Deleted image: {image['src']}")
                except Exception as e:
                    current_app.logger.warning(f"Failed to delete image: {str(e)}")
            
            return '', 204
        except Exception as e:
            current_app.logger.error(f"Error deleting product: {str(e)}")
            api.abort(500, str(e), error_code='PRODUCT_DELETE_ERROR')

    @products_ns.doc(
        description='Duplicate a product',
        responses={
            200: ('Product duplicated successfully', product),
            401: ('Unauthorized - Invalid or missing API key', error_response),
            404: ('Product not found', error_response),
            500: ('Internal server error', error_response)
        }
    )
    @products_ns.response(200, 'Product duplicated successfully')
    def post(self, id):
        """
        Duplicate a product
        
        Creates a copy of an existing product with all its variants, images, and metadata.
        The new product will have "(Copy)" appended to its title.
        """
        try:
            return get_shopify_service().duplicate_product(id)
        except Exception as e:
            api.abort(500, str(e), error_code='PRODUCT_DUPLICATE_ERROR')

# Theme endpoints
@themes_ns.route('/')
class ThemeList(Resource):
    @themes_ns.doc('list_themes')
    @themes_ns.marshal_list_with(theme)
    def get(self):
        """List all themes"""
        return get_shopify_service().get_themes()

@themes_ns.route('/<id>/assets')
@themes_ns.param('id', 'Theme identifier')
class ThemeAssets(Resource):
    @themes_ns.doc('get_theme_assets')
    @themes_ns.marshal_list_with(asset)
    def get(self, id):
        """Get theme assets"""
        return get_shopify_service().get_theme_assets(id)

# AI endpoints
# New models for generate-content2
generate_content2_request = api.model('GenerateContent2Request', {
    'url': fields.String(required=True, description='URL to generate content from'),
    'language': fields.String(required=True, description='Language code (en, el, pl)', default='en', enum=['en', 'el', 'pl'])
})

scraping_result = api.model('ScrapingResult', {
    'status': fields.String(description='Scraping status (success/warning)', enum=['success', 'warning']),
    'warning': fields.String(description='Warning message if any'),
    'images': fields.List(fields.Nested(api.model('ScrapedImage', {
        'src': fields.String(description='Image URL'),
        'alt': fields.String(description='Image alt text'),
        'width': fields.String(description='Image width'),
        'height': fields.String(description='Image height'),
        'class': fields.String(description='Image CSS classes')
    })))
})

token_pricing = api.model('TokenPricing', {
    'input_cost': fields.Float(description='Input tokens cost'),
    'output_cost': fields.Float(description='Output tokens cost'),
    'cache_cost': fields.Float(description='Cache cost'),
    'total_cost': fields.Float(description='Total cost')
})

token_usage = api.model('TokenUsage2', {
    'input_tokens': fields.Integer(description='Number of input tokens'),
    'output_tokens': fields.Integer(description='Number of output tokens'),
    'pricing': fields.Nested(token_pricing)
})

metrics = api.model('Metrics2', {
    'response_time': fields.Float(description='Total processing time in seconds'),
    'token_usage': fields.Nested(token_usage)
})

generate_content2_response = api.model('GenerateContent2Response', {
    'success': fields.Boolean(description='Operation success status'),
    'url': fields.String(description='Processed URL'),
    'scraping': fields.Nested(scraping_result),
    'analysis': fields.Nested(api.model('AnalysisResult', {
        'platform_detection': fields.Raw(description='Detected platform information'),
        'product_images': fields.List(fields.String(description='Product image URLs')),
        'content': fields.Raw(description='Generated content')
    })),
    'metrics': fields.Nested(metrics)
})

@ai_ns.route('/generate-content2')
class GenerateContent2(Resource):
    @ai_ns.doc('generate_content2',
        description='Enhanced AI content generation from URL with advanced scraping and analysis',
        responses={
            200: ('Content generated successfully', generate_content2_response),
            400: ('Invalid request parameters', error_response),
            500: ('Server error', error_response)
        })
    @ai_ns.expect(generate_content2_request)
    @ai_ns.marshal_with(generate_content2_response)
    def post(self):
        """Generate enhanced AI content from URL with advanced scraping and analysis"""
        try:
            start_time = time.time()
            data = request.get_json()
            
            if not data or 'url' not in data:
                api.abort(400, "URL is required in request body", error_code='MISSING_URL')
                
            url = data['url']
            language = data.get('language', 'en')
            
            # Validate language
            if language not in ['en', 'el', 'pl']:
                api.abort(400, "Invalid language. Supported languages are: en, el, pl", error_code='INVALID_LANGUAGE')
                
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Initialize response structure
            response_data = {
                'success': True,
                'url': url,
                'scraping': {},
                'analysis': {},
                'metrics': {}
            }
            
            # Initialize content service
            content_service = ContentService()
            
            # Step 1: Extract images and content
            try:
                html_content = content_service.fetch_with_advanced_retry(url)
                cleaned_content, images = content_service.clean_html(html_content)
                warning_message = None
                scraping_status = 'success'
            except Exception as e:
                if 'SSL' in str(e):
                    html_content = content_service.fetch_with_advanced_retry(url.replace('https://', 'http://'))
                    cleaned_content, images = content_service.clean_html(html_content)
                    warning_message = "⚠️ Warning: This website has SSL certificate issues. Be careful with sensitive information."
                    scraping_status = 'warning'
                else:
                    raise
            
            # Update scraping section
            response_data['scraping'] = {
                'status': scraping_status,
                'warning': warning_message,
                'images': images
            }
            
            # Step 2: Generate content and analyze
            analysis_result = content_service.analyze_content(url, cleaned_content, images, language)
            
            # Update analysis section
            response_data['analysis'] = {
                'platform_detection': analysis_result['platform_detection'],
                'product_images': analysis_result['product_images'],
                'content': analysis_result['content']
            }
            
            # Calculate metrics
            total_time = round(time.time() - start_time, 2)
            
            # Update metrics section with actual token usage
            response_data['metrics'] = {
                'response_time': total_time,
                'token_usage': analysis_result['token_usage']
            }
            
            return response_data
            
        except Exception as e:
            error_message = str(e)
            if "certificate verify failed" in error_message:
                error_message = "The website's security certificate has expired or is invalid. You may try again, but proceed with caution."
            elif any(x in error_message.lower() for x in ['403', 'forbidden', 'access denied']):
                error_message = "Access denied. The website might be blocking automated access."
            
            current_app.logger.error(f"Error in generate-content2: {error_message}")
            api.abort(500, error_message, error_code='CONTENT_GENERATION_ERROR')

optimize_request = api.model('OptimizeRequest', {
    'images': fields.List(fields.String, required=True, description='Image URLs'),
    'options': fields.Nested(api.model('OptimizeOptions', {
        'format': fields.String(enum=['jpeg', 'webp', 'png']),
        'quality': fields.Integer(min=1, max=100),
        'max_width': fields.Integer(),
        'max_height': fields.Integer()
    }))
})

optimize_response = api.model('OptimizeResponse', {
    'images': fields.List(fields.Nested(api.model('OptimizedImage', {
        'original_url': fields.String(required=True),
        'optimized_url': fields.String(required=True),
        'size_reduction': fields.Integer(description='Size reduction in percentage')
    })))
})

@images_ns.route('/optimize-images')
class OptimizeImages(Resource):
    @images_ns.doc('optimize_images')
    @images_ns.expect(optimize_request)
    @images_ns.marshal_with(optimize_response)
    def post(self):
        """Optimize images"""
        data = api.payload
        return {'images': get_shopify_service().optimize_images(data['images'], data.get('options', {}))}

# Convert the template endpoint to Flask-RESTX style
template_request = api.model('TemplateRequest', {
    'source': fields.String(required=True, description='Source template name'),
    'content': fields.Raw(description='Generated content'),
    'images': fields.List(fields.Raw(description='Image data'))
})

template_response = api.model('TemplateResponse', {
    'success': fields.Boolean(description='Operation success status'),
    'template_suffix': fields.String(description='Generated template suffix')
})

@templates_ns.route('/create')
class CreateTemplate(Resource):
    @templates_ns.doc('create_template')
    @templates_ns.expect(template_request)
    @templates_ns.response(201, 'Template created successfully', template_response)
    @templates_ns.response(500, 'Template creation failed')
    def post(self):
        """Create a new template asset in the active theme"""
        try:
            data = api.payload
            source_template = data.get('source')
            generated_content = data.get('content', {})
            extracted_images = data.get('images', [])
            
            # Debug: Log received content and images
            current_app.logger.info('==================== RECEIVED CONTENT ====================')
            current_app.logger.info(json.dumps(generated_content, indent=2))
            current_app.logger.info('==================== RECEIVED IMAGES ====================')
            current_app.logger.info(json.dumps(extracted_images, indent=2))
            
            # Read the template file
            template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', source_template)
            with open(template_path, 'r') as f:
                template_content = f.read()
                template_content = '\n'.join(line for line in template_content.split('\n') 
                                           if not line.strip().startswith('/*') and 
                                           not line.strip().startswith('*') and 
                                           not line.strip().startswith('*/'))
                template_json = json.loads(template_content)
            
            def convert_to_shopify_image_url(cdn_url):
                """Convert Shopify CDN URL to shopify://shop_images format"""
                try:
                    import re
                    match = re.search(r'(?:/files/[^/]+/[^/]+/[^/]+/)?([^/]+\.[a-zA-Z]+)(?:\?.*)?$', cdn_url)
                    if match:
                        filename = match.group(1)
                        return f"shopify://shop_images/{filename}"
                    current_app.logger.warning(f"Could not extract filename from URL: {cdn_url}")
                    return None
                except Exception as e:
                    current_app.logger.error(f"Error converting image URL: {str(e)}")
                    return None

            # Get available images for replacement
            available_images = []
            if extracted_images and len(extracted_images) > 0:
                for img in extracted_images:
                    shopify_url = convert_to_shopify_image_url(img['src'])
                    if shopify_url:
                        available_images.append(shopify_url)
                        current_app.logger.info(f"Converted {img['src']} to {shopify_url}")
                    else:
                        current_app.logger.warning(f"Skipping invalid image URL: {img['src']}")

            def replace_content_preserve_tags(original_value, new_content):
                """Replace content while preserving HTML tags"""
                if not ('<' in str(original_value) and '>' in str(original_value)):
                    return new_content
                import re
                tags = re.findall(r'<[^>]+>', str(original_value))
                if len(tags) >= 2:
                    opening_tag = tags[0]
                    closing_tag = tags[-1]
                    return f"{opening_tag}{new_content}{closing_tag}"
                return new_content

            # First update text content
            for key, value in generated_content.items():
                path_parts = key.split('.')
                current = template_json
                for part in path_parts[:-1]:
                    if part not in current:
                        current_app.logger.warning(f'Path not found: {key}')
                        continue
                    current = current[part]
                
                if path_parts[-1] in current:
                    if isinstance(value, (str, list)):
                        original_value = current[path_parts[-1]]
                        if 'percent_value' in key:
                            try:
                                value = int(value)
                            except:
                                value = 95
                        else:
                            if isinstance(value, list):
                                value = value[0] if value else ""
                            value = str(value).strip()
                            value = replace_content_preserve_tags(original_value, value)
                    
                    current_app.logger.info(f'Setting text {key} = {value}')
                    current[path_parts[-1]] = value

            # Update all image sections recursively
            def update_images_recursive(obj, parent_key=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        full_key = f"{parent_key}.{key}" if parent_key else key
                        if key == "image" and isinstance(value, str):
                            available_unused_images = [img for img in available_images if img not in used_images]
                            if available_unused_images:
                                selected_image = random.choice(available_unused_images)
                                used_images.add(selected_image)
                                obj[key] = selected_image
                                current_app.logger.info(f'Setting image at {full_key} = {selected_image}')
                        else:
                            update_images_recursive(value, full_key)
                elif isinstance(obj, list):
                    for item in obj:
                        update_images_recursive(item, parent_key)

            # Keep track of used images
            used_images = set()
            
            # Update images recursively
            update_images_recursive(template_json)
            
            # Debug: Log final template structure
            current_app.logger.info('==================== FINAL TEMPLATE ====================')
            current_app.logger.info(json.dumps(template_json, indent=2))
            
            # Generate random suffix
            template_suffix = generate_random_suffix()
            
            # Create asset in theme
            asset_key = f'templates/product.{template_suffix}.json'
            current_app.logger.info(f'Creating asset with key: {asset_key}')
            
            try:
                get_shopify_service().create_asset(asset_key, template_json)
            except Exception as asset_error:
                current_app.logger.error('==================== ASSET CREATION ERROR ====================')
                current_app.logger.error(f'Error details: {str(asset_error)}')
                current_app.logger.error('Template that caused error:')
                current_app.logger.error(json.dumps(template_json, indent=2))
                raise
            
            return {
                'success': True,
                'template_suffix': template_suffix
            }, 201
            
        except Exception as e:
            current_app.logger.error(f'Error creating template: {str(e)}')
            api.abort(500, f'Failed to create template: {str(e)}')

def generate_random_suffix(length=10):
    """Generate a random string of digits."""
    return ''.join(random.choices(string.digits, k=length))

# Store connection endpoint
@store_ns.route('/connect')
class ConnectStore(Resource):
    @store_ns.doc('connect_store')
    @store_ns.expect(store_connection_request)
    @store_ns.marshal_with(store_connection_response)
    def post(self):
        """Connect a Shopify store and save credentials"""
        try:
            data = api.payload
            store_url = data['store_url'].strip()
            api_key = data['api_key'].strip()
            
            # Validate store URL format
            if not store_url.endswith('.myshopify.com'):
                store_url += '.myshopify.com'
            
            # Initialize temporary service to validate credentials
            temp_service = ShopifyService()
            temp_service.initialize(store_url, api_key)
            
            # Test connection by fetching themes
            themes = temp_service.get_themes()
            if not themes:
                api.abort(400, 'Could not fetch store data. Please verify your credentials.')
            
            # Get current user from session
            if not hasattr(current_app, 'supabase'):
                api.abort(500, 'Database connection not initialized')
            
            user_id = session.get('user_id')
            if not user_id:
                api.abort(401, 'User not authenticated')
            
            # Save credentials to Supabase
            current_app.supabase.table('users').update({
                'shopify_store_url': store_url,
                'shopify_api_key': api_key,
                'store_connected': True,
                'connected_at': datetime.utcnow().isoformat()
            }).eq('id', user_id).execute()
            
            # Update session
            session['store_connected'] = True
            session['store_url'] = store_url
            
            return {
                'message': 'Store connected successfully',
                'store_url': store_url
            }, 200
            
        except Exception as e:
            current_app.logger.error(f'Store connection error: {str(e)}')
            api.abort(500, f'Failed to connect store: {str(e)}')

@analytics_ns.route('/dashboard')
class AnalyticsDashboard(Resource):
    @analytics_ns.doc(
        description='Get a summary of all analytics metrics for the dashboard',
        params={'time_range': 'Time range for analytics (7d, 30d, 90d, 1y)'}
    )
    @analytics_ns.response(200, 'Success', dashboard_summary)
    @analytics_ns.response(500, 'Internal server error', error_response)
    def get(self):
        """Get dashboard analytics summary"""
        try:
            time_range = request.args.get('time_range', '30d')
            return get_analytics_service().get_dashboard_summary(time_range)
        except Exception as e:
            api.abort(500, str(e))

@analytics_ns.route('/products')
class ProductAnalytics(Resource):
    @analytics_ns.doc(
        description='Get product-related analytics',
        params={'time_range': 'Time range for analytics (7d, 30d, 90d, 1y)'}
    )
    @analytics_ns.response(200, 'Success', product_analytics)
    @analytics_ns.response(500, 'Internal server error', error_response)
    def get(self):
        """Get product analytics"""
        try:
            time_range = request.args.get('time_range', '30d')
            return get_analytics_service().get_product_analytics(time_range)
        except Exception as e:
            api.abort(500, str(e))

@analytics_ns.route('/orders')
class OrderAnalytics(Resource):
    @analytics_ns.doc(
        description='Get order-related analytics',
        params={'time_range': 'Time range for analytics (7d, 30d, 90d, 1y)'}
    )
    @analytics_ns.response(200, 'Success', order_analytics)
    @analytics_ns.response(500, 'Internal server error', error_response)
    def get(self):
        """Get order analytics"""
        try:
            time_range = request.args.get('time_range', '30d')
            return get_analytics_service().get_order_analytics(time_range)
        except Exception as e:
            api.abort(500, str(e))

@analytics_ns.route('/themes')
class ThemeAnalytics(Resource):
    @analytics_ns.doc(
        description='Get theme-related analytics',
        params={'time_range': 'Time range for analytics (7d, 30d, 90d, 1y)'}
    )
    @analytics_ns.response(200, 'Success', theme_analytics)
    @analytics_ns.response(500, 'Internal server error', error_response)
    def get(self):
        """Get theme analytics"""
        try:
            time_range = request.args.get('time_range', '30d')
            return get_analytics_service().get_theme_analytics(time_range)
        except Exception as e:
            api.abort(500, str(e))

@analytics_ns.route('/performance')
class StorePerformance(Resource):
    @analytics_ns.doc(
        description='Get store performance analytics',
        params={'time_range': 'Time range for analytics (7d, 30d, 90d, 1y)'}
    )
    @analytics_ns.response(200, 'Success', store_performance)
    @analytics_ns.response(500, 'Internal server error', error_response)
    def get(self):
        """Get store performance analytics"""
        try:
            time_range = request.args.get('time_range', '30d')
            return get_analytics_service().get_store_performance(time_range)
        except Exception as e:
            api.abort(500, str(e)) 