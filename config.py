import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Shopify Configuration
    SHOP_URL = os.environ.get('SHOPIFY_SHOP_URL')
    ACCESS_TOKEN = os.environ.get('SHOPIFY_ACCESS_TOKEN')
    API_VERSION = os.environ.get('SHOPIFY_API_VERSION', '2024-04')
    SHOPIFY_BASE_URL = f"https://{SHOP_URL}/admin/api/{API_VERSION}"
    
    # Gemini Configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

    HEADERS = {
        'X-Shopify-Access-Token': ACCESS_TOKEN,
        'Content-Type': 'application/json'
    }

    # Supabase Configuration
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    
    # Session Configuration
    SESSION_TYPE = 'filesystem'
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