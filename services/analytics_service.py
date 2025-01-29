from flask import current_app
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

class AnalyticsService:
    def __init__(self):
        self.shopify_service = None

    def _init_shopify(self):
        """Initialize Shopify service if not already initialized"""
        if not self.shopify_service:
            from services.shopify_service import ShopifyService
            self.shopify_service = ShopifyService()

    def get_product_analytics(self, time_range: str = '30d') -> Dict[str, Any]:
        """Get product-related analytics
        
        Args:
            time_range (str): Time range for analytics (7d, 30d, 90d, 1y)
            
        Returns:
            Dict containing product analytics data
        """
        self._init_shopify()
        
        try:
            products = self.shopify_service.get_products()
            
            # Calculate product metrics
            total_products = len(products)
            active_products = len([p for p in products if p.get('status') == 'active'])
            total_variants = sum(len(p.get('variants', [])) for p in products)
            
            # Analyze product types and vendors
            product_types = {}
            vendors = {}
            price_ranges = {
                '0-10': 0,
                '10-25': 0,
                '25-50': 0,
                '50-100': 0,
                '100+': 0
            }
            
            for product in products:
                # Track product types
                product_type = product.get('product_type', 'Uncategorized')
                product_types[product_type] = product_types.get(product_type, 0) + 1
                
                # Track vendors
                vendor = product.get('vendor', 'Unknown')
                vendors[vendor] = vendors.get(vendor, 0) + 1
                
                # Analyze price ranges
                for variant in product.get('variants', []):
                    price = float(variant.get('price', 0))
                    if price <= 10:
                        price_ranges['0-10'] += 1
                    elif price <= 25:
                        price_ranges['10-25'] += 1
                    elif price <= 50:
                        price_ranges['25-50'] += 1
                    elif price <= 100:
                        price_ranges['50-100'] += 1
                    else:
                        price_ranges['100+'] += 1
            
            return {
                'summary': {
                    'total_products': total_products,
                    'active_products': active_products,
                    'total_variants': total_variants,
                },
                'product_types': [
                    {'type': k, 'count': v} 
                    for k, v in sorted(product_types.items(), key=lambda x: x[1], reverse=True)
                ],
                'vendors': [
                    {'name': k, 'count': v} 
                    for k, v in sorted(vendors.items(), key=lambda x: x[1], reverse=True)
                ],
                'price_distribution': [
                    {'range': k, 'count': v} 
                    for k, v in price_ranges.items()
                ]
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting product analytics: {str(e)}")
            raise

    def get_order_analytics(self, time_range: str = '30d') -> Dict[str, Any]:
        """Get order-related analytics
        
        Args:
            time_range (str): Time range for analytics (7d, 30d, 90d, 1y)
            
        Returns:
            Dict containing order analytics data
        """
        self._init_shopify()
        
        try:
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
                start_date = end_date - timedelta(days=30)

            orders = self.shopify_service.get_orders(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            # Calculate order metrics
            total_orders = len(orders)
            total_revenue = sum(float(order.get('total_price', 0)) for order in orders)
            avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
            
            # Analyze orders by day
            daily_orders = {}
            daily_revenue = {}
            
            for order in orders:
                date = order.get('created_at', '').split('T')[0]
                if date:
                    daily_orders[date] = daily_orders.get(date, 0) + 1
                    daily_revenue[date] = daily_revenue.get(date, 0) + float(order.get('total_price', 0))
            
            return {
                'summary': {
                    'total_orders': total_orders,
                    'total_revenue': round(total_revenue, 2),
                    'average_order_value': round(avg_order_value, 2)
                },
                'daily_metrics': [
                    {
                        'date': date,
                        'orders': daily_orders.get(date, 0),
                        'revenue': round(daily_revenue.get(date, 0), 2)
                    }
                    for date in sorted(set(daily_orders.keys()))
                ]
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting order analytics: {str(e)}")
            raise

    def get_theme_analytics(self, time_range: str = '30d') -> Dict[str, Any]:
        """Get theme-related analytics
        
        Args:
            time_range (str): Time range for analytics (7d, 30d, 90d, 1y)
            
        Returns:
            Dict containing theme analytics data
        """
        self._init_shopify()
        
        try:
            themes = self.shopify_service.get_themes()
            
            # Analyze themes
            total_themes = len(themes)
            active_theme = next((theme for theme in themes if theme.get('role') == 'main'), None)
            theme_statuses = {
                'live': len([t for t in themes if t.get('role') == 'main']),
                'unpublished': len([t for t in themes if t.get('role') == 'unpublished']),
                'demo': len([t for t in themes if t.get('role') == 'demo'])
            }
            
            return {
                'summary': {
                    'total_themes': total_themes,
                    'active_theme': active_theme.get('name') if active_theme else None
                },
                'theme_statuses': [
                    {'status': k, 'count': v}
                    for k, v in theme_statuses.items()
                ],
                'themes': [
                    {
                        'name': theme.get('name'),
                        'role': theme.get('role'),
                        'created_at': theme.get('created_at')
                    }
                    for theme in themes
                ]
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting theme analytics: {str(e)}")
            raise

    def get_store_performance(self, time_range: str = '30d') -> Dict[str, Any]:
        """Get store performance analytics
        
        Args:
            time_range (str): Time range for analytics (7d, 30d, 90d, 1y)
            
        Returns:
            Dict containing store performance data
        """
        self._init_shopify()
        
        try:
            analytics_data = self.shopify_service.get_analytics_data(time_range)
            
            return {
                'traffic': {
                    'total_views': analytics_data.get('analytics', {}).get('total_views', 0),
                    'unique_visitors': analytics_data.get('analytics', {}).get('unique_visitors', 0),
                    'avg_session_duration': analytics_data.get('analytics', {}).get('avg_session_duration', 0),
                    'bounce_rate': analytics_data.get('analytics', {}).get('bounce_rate', 0)
                },
                'top_referrers': analytics_data.get('analytics', {}).get('top_referrers', []),
                'device_breakdown': analytics_data.get('analytics', {}).get('device_breakdown', {})
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting store performance: {str(e)}")
            raise

    def get_dashboard_summary(self, time_range: str = '30d') -> Dict[str, Any]:
        """Get a summary of all analytics for the dashboard
        
        Args:
            time_range (str): Time range for analytics (7d, 30d, 90d, 1y)
            
        Returns:
            Dict containing dashboard summary data
        """
        try:
            product_analytics = self.get_product_analytics(time_range)
            order_analytics = self.get_order_analytics(time_range)
            theme_analytics = self.get_theme_analytics(time_range)
            store_performance = self.get_store_performance(time_range)
            
            return {
                'products': product_analytics['summary'],
                'orders': order_analytics['summary'],
                'themes': theme_analytics['summary'],
                'performance': store_performance['traffic'],
                'time_range': time_range
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting dashboard summary: {str(e)}")
            raise 