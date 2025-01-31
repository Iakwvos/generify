import os
from dotenv import load_dotenv
import logging

load_dotenv()

def validate_env_vars():
    required_vars = {
        'SHOPIFY_SHOP_URL': 'Shopify store URL is required',
        'SHOPIFY_ACCESS_TOKEN': 'Shopify access token is required',
        'GEMINI_API_KEY': 'Gemini API key is required',
        'SUPABASE_URL': 'Supabase URL is required',
        'SUPABASE_KEY': 'Supabase key is required',
        'FLASK_SECRET_KEY': 'Flask secret key is required'
    }
    
    missing_vars = []
    for var, message in required_vars.items():
        if not os.environ.get(var):
            missing_vars.append(message)
    
    if missing_vars:
        error_message = "Missing required environment variables:\n" + "\n".join(missing_vars)
        logging.error(error_message)
        raise EnvironmentError(error_message)

class Config:
    # Validate environment variables on startup
    validate_env_vars()
    
    # Shopify Configuration
    SHOP_URL = os.environ.get('SHOPIFY_SHOP_URL')
    ACCESS_TOKEN = os.environ.get('SHOPIFY_ACCESS_TOKEN')
    API_VERSION = os.environ.get('SHOPIFY_API_VERSION', '2024-04')
    SHOPIFY_BASE_URL = f"https://{SHOP_URL}/admin/api/{API_VERSION}"
    
    # Gemini Configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    HEADERS = {
        'X-Shopify-Access-Token': ACCESS_TOKEN,
        'Content-Type': 'application/json'
    }

    # Supabase Configuration
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    
    # Session Configuration
    SESSION_TYPE = 'filesystem'  # Default to filesystem
    if os.environ.get('REDIS_URL'):
        SESSION_TYPE = 'redis'
        SESSION_REDIS = os.environ.get('REDIS_URL')
        SESSION_USE_SIGNER = True
    
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    
    # Security Configuration
    REMEMBER_COOKIE_DURATION = 2592000  # 30 days
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True

    # Bing Image Search API
    BING_SEARCH_KEY = os.environ.get('BING_SEARCH_KEY', '')

    # Google Custom Search API
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', '')
    GOOGLE_SEARCH_CX = os.environ.get('GOOGLE_SEARCH_CX', '')

    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO') 