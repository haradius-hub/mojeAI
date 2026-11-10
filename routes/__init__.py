# routes/__init__.py
from .chat import chat_bp
from .config import config_bp
from .memory import memory_bp

def register_routes(app):
    app.register_blueprint(chat_bp)
    app.register_blueprint(config_bp)
    app.register_blueprint(memory_bp)
