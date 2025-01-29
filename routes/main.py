from flask import Blueprint, render_template, current_app, flash, jsonify, redirect, url_for, session
import requests
import google.generativeai as genai
from services.shopify_service import ShopifyService
from auth.decorators import login_required

main_bp = Blueprint('main', __name__)
shopify_service = ShopifyService()

@main_bp.route('/')
def landing():
    """Landing page view"""
    return render_template('landing.html')

@main_bp.route('/features')
def features():
    """Features page view"""
    return render_template('features.html')

@main_bp.route('/pricing')
def pricing():
    """Pricing page view"""
    return render_template('pricing.html')

@main_bp.route('/about')
def about():
    """About page view"""
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    """Contact page view"""
    return render_template('contact.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard view"""
    # Initialize default values
    products = []
    store_stats = {
        'total_products': 0,
        'total_themes': 0,
        'avg_price': '0.00'
    }
    error = None
    active_theme_id = None
    
    try:
        shopify_service = get_shopify_service()
        products = shopify_service.get_products()
        themes = shopify_service.get_themes()
        
        # Get active theme
        active_theme = next((theme for theme in themes if theme.get('role') == 'main'), None)
        active_theme_id = active_theme.get('id') if active_theme else None
        
        # Calculate average product price from variants
        total_price = 0.0
        total_variants = 0
        for product in products:
            for variant in product.get('variants', []):
                if variant.get('price'):
                    total_price += float(variant.get('price', 0))
                    total_variants += 1
        
        avg_price = total_price / total_variants if total_variants > 0 else 0
        
        # Update store stats with actual data
        store_stats.update({
            'total_products': len(products),
            'total_themes': len(themes),
            'avg_price': f"{avg_price:,.2f}"
        })
        
    except Exception as e:
        error_msg = "An unexpected error occurred. Please check your configuration and try again."
        current_app.logger.error(f"Error in dashboard route: {str(e)}")
        flash(error_msg, 'error')
        error = str(e)
    
    return render_template('dashboard.html', 
                         products=products, 
                         store_stats=store_stats,
                         error=error,
                         active_theme_id=active_theme_id,
                         ai_insights=None)  # Set to None initially

def get_shopify_service():
    """Get or create ShopifyService instance"""
    if not hasattr(current_app, 'shopify_service'):
        current_app.shopify_service = ShopifyService()
    return current_app.shopify_service

@main_bp.route('/ai-insights')
def get_ai_insights():
    """Get AI-generated insights about the store"""
    try:
        shopify_service = get_shopify_service()
        products = shopify_service.get_products()
        themes = shopify_service.get_themes()
        
        active_theme = next((theme for theme in themes if theme.get('role') == 'main'), None)
        store_stats = {
            'total_products': len(products),
            'total_themes': len(themes),
            'active_theme': {
                'name': active_theme.get('name', 'No active theme') if active_theme else 'No active theme'
            }
        }
        
        # Initialize Gemini AI
        genai.configure(api_key=current_app.config['GEMINI_API_KEY'])
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Create a more focused prompt
        prompt = f"""Analyze this Shopify store data and provide brief, actionable insights:

1. Products ({store_stats['total_products']} total):
💡 Quick analysis of product count and variety
💡 One key recommendation for product strategy

2. Theme Setup ({store_stats['total_themes']} themes):
💡 Brief assessment of theme usage
💡 One optimization suggestion for {store_stats['active_theme']['name']}

3. Quick Tips:
💡 Most impactful action to take now
💡 One performance optimization suggestion

Keep each insight to 1-2 sentences max. Focus on immediate, actionable advice."""
        
        response = model.generate_content(prompt)
        insights = [insight.strip() for insight in response.text.split('\n') if insight.strip() and '💡' in insight]
        
        return jsonify({'insights': insights})
        
    except Exception as e:
        current_app.logger.error(f"Failed to generate AI insights: {str(e)}")
        return jsonify({'insights': ["💡 AI insights temporarily unavailable"]})

@main_bp.route('/legal/<page>')
def legal(page):
    """Legal pages view (privacy policy, terms of service)"""
    if page not in ['privacy', 'terms']:
        return render_template('404.html'), 404
    return render_template(f'legal/{page}.html')

@main_bp.route('/support/<page>')
def support(page):
    """Support pages view (help center, system status)"""
    if page not in ['help', 'status']:
        return render_template('404.html'), 404
    return render_template(f'support/{page}.html')

@main_bp.route('/products')
@login_required
def products():
    """Products page view"""
    return render_template('products.html')

@main_bp.route('/ai-content')
@login_required
def ai_content():
    """AI Content page view"""
    return render_template('ai_content.html')

@main_bp.route('/templates')
@login_required
def templates():
    """Templates page view"""
    return render_template('templates.html')

@main_bp.route('/store-settings')
@login_required
def store_settings():
    """Store settings page view"""
    return render_template('store_settings.html')

@main_bp.route('/account-settings')
@login_required
def account_settings():
    """Account settings page view"""
    return render_template('account_settings.html')

@main_bp.route('/help')
def help():
    """Help page view"""
    return render_template('help.html') 