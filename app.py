from flask import Flask, render_template
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

# Load environment variables
load_dotenv()

def create_app():
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
        app.shopify_service = ShopifyService()
        app.gemini_service = GeminiService()
        app.image_service = ImageService()
        app.platform_service = PlatformService()
    
    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error/404.html'), 404

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True) 