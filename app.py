# app.py
import os
import sys

# TOTO JE KLÍČOVÉ: Řekne Pythonu, aby hledal moduly ve složce, kde leží app.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template
from config import Config
from routes import register_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    # Bezpečný výchozí limit; aplikace je v této etapě určena pouze pro localhost.
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
    
    # Inicializace složek při startu
    Config.init_dirs()
    
    # Registrace všech API endpointů (chat, config, pamet)
    register_routes(app)
    
    # Zobrazení hlavní stránky
    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("=" * 60)
    print("🤖 MojeAI - Portabilní asistent s pamětí (Refaktor v0.2)")
    print("=" * 60)
    print("🌐 Otevři v prohlížeči: http://localhost:5000")
    print("=" * 60)
    port = int(os.environ.get('MOJEAI_PORT', '5000'))
    app.run(debug=False, host='127.0.0.1', port=port)