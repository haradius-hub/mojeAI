# routes/__init__.py
from .chat import chat_bp
from .config import config_bp
from .memory import memory_bp
from .projects import projects_bp
from core.projects import project_manager


def register_routes(app):
    project_manager.init()
    app.register_blueprint(chat_bp)
    app.register_blueprint(config_bp)
    app.register_blueprint(memory_bp)
    app.register_blueprint(projects_bp)
