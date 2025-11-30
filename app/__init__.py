import os
from flask import Flask
from .config import Config
from .routes import register_routes

def create_app():
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.config.from_object(Config())
    # Set cache max age for static files to 1 week (604800 seconds)
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 604800
    app.url_map.strict_slashes = False
    register_routes(app)
    return app
