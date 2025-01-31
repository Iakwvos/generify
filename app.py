from flask import Flask, render_template, jsonify, request
from routes.main import main_bp
from routes.api import api_bp
from routes.pages import pages
from services.shopify_service import ShopifyService
from services.gemini_service import GeminiService
from services.image_service import ImageService
from services.platform_service import PlatformService
from dotenv import load_dotenv
import os
from flask_session import Session
from config import Config
from auth import auth_bp
import jinja2
import logging
import traceback
import redis
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def check_required_env_vars():
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'FLASK_SECRET_KEY',
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

def check_services_health():
    """Check the health of all services"""
    health_status = {
        "session_storage": {
            "type": "filesystem",
            "status": True
        },
        "supabase": False,
        "shopify": False,
        "services_initialized": False
    }
    
    # Check Redis if configured
    if os.environ.get('REDIS_URL'):
        try:
            redis_client = redis.from_url(os.environ.get('REDIS_URL'))
            redis_client.ping()
            health_status["session_storage"] = {
                "type": "redis",
                "status": True
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            health_status["session_storage"] = {
                "type": "redis",
                "status": False,
                "error": str(e)
            }
    
    # Check Supabase connection
    try:
        # Basic check if Supabase credentials are configured
        if os.environ.get('SUPABASE_URL') and os.environ.get('SUPABASE_KEY'):
            health_status["supabase"] = True
    except Exception as e:
        logger.error(f"Supabase health check failed: {str(e)}")
    
    # Check Shopify connection
    try:
        if os.environ.get('SHOPIFY_SHOP_URL') and os.environ.get('SHOPIFY_ACCESS_TOKEN'):
            health_status["shopify"] = True
    except Exception as e:
        logger.error(f"Shopify health check failed: {str(e)}")
    
    return health_status

def create_app():
    # Log startup information
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Starting application on port {port}")
    
    # Check environment variables before creating app
    check_required_env_vars()
    
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(pages)  # Pages blueprint for dashboard and analytics
    app.register_blueprint(main_bp)  # Main blueprint for landing and marketing pages
    app.register_blueprint(auth_bp)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Initialize Flask-Session
    Session(app)
    
    # Initialize services
    with app.app_context():
        try:
            app.shopify_service = ShopifyService()
            app.gemini_service = GeminiService()
            app.image_service = ImageService()
            app.platform_service = PlatformService()
            logger.info("All services initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing services: {str(e)}")
            raise
    
    # Root endpoint for basic health check
    @app.route('/')
    def root():
        return jsonify({"status": "ok", "message": "Application is running"}), 200
    
    # Detailed health check endpoint
    @app.route('/health')
    def health_check():
        health_status = check_services_health()
        status_code = 200 if all(health_status.values()) else 503
        response = {
            "status": "healthy" if status_code == 200 else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": health_status
        }
        return jsonify(response), status_code
    
    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        logger.warning(f"404 error: {request.url}")
        return render_template('error/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        error_details = {
            'error': str(e),
            'traceback': traceback.format_exc(),
            'endpoint': request.endpoint,
            'method': request.method,
            'url': request.url,
            'timestamp': datetime.utcnow().isoformat()
        }
        logger.error(f"500 error: {error_details}")
        return render_template('error/500.html'), 500

    @app.before_request
    def log_request_info():
        logger.info(f"Request: {request.method} {request.url}")

    @app.after_request
    def log_response_info(response):
        logger.info(f"Response: {response.status}")
        return response

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Starting development server on port {port}")
    app.run(host='0.0.0.0', port=port) 