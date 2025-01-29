import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Shopify Configuration
    SHOP_URL = "k7bseq-qf.myshopify.com"
    ACCESS_TOKEN = "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"
    API_VERSION = "2024-04"
    SHOPIFY_BASE_URL = f"https://{SHOP_URL}/admin/api/{API_VERSION}"
    
    # Gemini Configuration
    GEMINI_API_KEY = "AIzaSyArQknln_YjGGcFBEXoUPqDone7FM7uFsg"
    
    # Flask Configuration
    SECRET_KEY = os.urandom(24)
    DEBUG = True

    HEADERS = {
        'X-Shopify-Access-Token': ACCESS_TOKEN,
        'Content-Type': 'application/json'
    }

    # Supabase Configuration
    SUPABASE_URL = "https://qszwxkazjxjfqosyoqvq.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFzend4a2F6anhqZnFvc3lvcXZxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzc4MzE0NjYsImV4cCI6MjA1MzQwNzQ2Nn0.ogoi4MlkTQh4yQ50ilWxFlPpIhEIVte237nVEUrtrZk"
    
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