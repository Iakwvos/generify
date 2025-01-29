from flask import Blueprint, render_template, jsonify, request, current_app, flash
from datetime import datetime, timedelta
import random
from services.shopify_service import ShopifyService
from services.analytics_service import AnalyticsService
from auth.decorators import login_required

pages = Blueprint('pages', __name__)

def get_shopify_service():
    """Get or create ShopifyService instance"""
    if not hasattr(current_app, 'shopify_service'):
        current_app.shopify_service = ShopifyService()
    return current_app.shopify_service

def get_analytics_service():
    """Get or create AnalyticsService instance"""
    if not hasattr(current_app, 'analytics_service'):
        current_app.analytics_service = AnalyticsService()
    return current_app.analytics_service

@pages.route('/dashboard')
def dashboard():
    """Render the main dashboard page."""
    # Initialize default values
    products = []
    store_stats = {
        'total_products': 0,
        'total_themes': 0,
        'inventory_value': '0.00',
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
        
        # Calculate average product price and inventory value from variants
        total_price = 0.0
        total_inventory_value = 0.0
        total_variants = 0
        for product in products:
            for variant in product.get('variants', []):
                if variant.get('price'):
                    price = float(variant.get('price', 0))
                    inventory = int(variant.get('inventory_quantity', 0))
                    total_price += price
                    total_inventory_value += price * inventory
                    total_variants += 1
        
        avg_price = total_price / total_variants if total_variants > 0 else 0
        
        # Update store stats with actual data
        store_stats.update({
            'total_products': len(products),
            'total_themes': len(themes),
            'inventory_value': f"{total_inventory_value:,.2f}",
            'avg_price': f"{avg_price:,.2f}"
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in dashboard route: {str(e)}")
        error = str(e)

    return render_template('dashboard.html', 
                         active_page='dashboard',
                         products=products, 
                         store_stats=store_stats,
                         error=error,
                         active_theme_id=active_theme_id)

@pages.route('/analytics')
@login_required
def analytics():
    """Render the analytics page with data from various sources."""
    try:
        # Get time range from query parameters, default to 30 days
        time_range = request.args.get('time_range', '30d')
        
        # Initialize analytics service
        analytics_service = get_analytics_service()
        
        # Get analytics data
        analytics_data = analytics_service.get_dashboard_summary(time_range)
        
        return render_template(
            'analytics.html',
            analytics=analytics_data,
            active_page='analytics'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error in analytics route: {str(e)}")
        flash("Failed to load analytics data. Please try again later.", "error")
        return render_template(
            'analytics.html',
            analytics=None,
            error=str(e),
            active_page='analytics'
        )

@pages.route('/settings')
def settings():
    """Render the settings page with current settings."""
    # Mock settings data - in production, this would come from a database
    settings_data = {
        'shopify_url': '',
        'api_key': '',
        'api_secret': '',
        'email_notifications': True,
        'order_alerts': True,
        'stock_alerts': False,
        'currency': 'USD',
        'timezone': 'UTC',
        'dark_mode': True
    }
    
    return render_template('settings.html', settings=settings_data, active_page='settings')

@pages.route('/api/settings/update', methods=['POST'])
def update_settings():
    """Update user settings."""
    try:
        settings = request.get_json()
        # In production, save these settings to a database
        # For now, just return success
        return jsonify({'status': 'success', 'message': 'Settings updated successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400 