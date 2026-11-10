# routes/config.py
import os
import glob
import subprocess
import platform
from flask import Blueprint, request, jsonify
from config import Config
from core.providers import Providers

config_bp = Blueprint('config', __name__)

@config_bp.route('/api/config', methods=['GET'])
def get_config():
    return jsonify({
        'config': Config.nacti(),
        'dostupne_modele': Providers.dostupne_modely()
    })

@config_bp.route('/api/config', methods=['POST'])
def set_config():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'status': 'error', 'zprava': 'Očekávána JSON data.'}), 400

    config = Config.nacti()
    povolene = {
        'internet': bool, 'smart_search': bool, 'pouzit_gpu': bool,
        'max_vzpominek': int, 'gpu_vrstev': int, 'n_ctx': int,
        'n_threads': int, 'vychozi_model': str,
    }
    limity = {
        'max_vzpominek': (0, 30), 'gpu_vrstev': (0, 200),
        'n_ctx': (512, 32768), 'n_threads': (1, 64),
    }
    for key, value in data.items():
        if key not in povolene:
            continue
        expected = povolene[key]
        if expected is int:
            if isinstance(value, bool) or not isinstance(value, int):
                return jsonify({'status': 'error', 'zprava': f'Neplatná hodnota: {key}'}), 400
            low, high = limity[key]
            if not low <= value <= high:
                return jsonify({'status': 'error', 'zprava': f'Hodnota {key} je mimo povolený rozsah.'}), 400
        elif not isinstance(value, expected):
            return jsonify({'status': 'error', 'zprava': f'Neplatná hodnota: {key}'}), 400
        config[key] = value
    Config.uloz(config)
    return jsonify({'status': 'ok', 'config': config})

@config_bp.route('/api/config/keys', methods=['POST'])
def uloz_klic():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'status': 'error', 'zprava': 'Očekávána JSON data.'}), 400
    provider = data.get('provider')
    klic = data.get('key')
    if not provider or not klic:
        return jsonify({'status': 'error', 'zprava': 'Chybí provider nebo klíč'})
    
    try:
        Providers.uloz_klic(provider, klic)
    except ValueError as e:
        return jsonify({'status': 'error', 'zprava': str(e)}), 400
    return jsonify({'status': 'ok'})

@config_bp.route('/api/prompt', methods=['POST'])
def nastav_prompt():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'status': 'error', 'zprava': 'Očekávána JSON data.'}), 400
    prompt = data.get('prompt')
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 12000:
        return jsonify({'status': 'error', 'zprava': 'Prompt musí mít 1 až 12 000 znaků.'}), 400
    config = Config.nacti()
    config['system_prompt'] = prompt
    Config.uloz(config)
    return jsonify({'status': 'ok'})

@config_bp.route('/api/gpu-info', methods=['GET'])
def get_gpu_info():
    """Zjistí dostupnost GPU na Windows i Linuxu."""
    system = platform.system()
    gpu_nazvy = []
    
    try:
        if system == 'Windows':
            # Zkusíme WMIC (starší Windows)
            try:
                result = subprocess.run(
                    ['wmic', 'path', 'win32_VideoController', 'get', 'name'],
                    capture_output=True, text=True, timeout=5
                )
                gpu_nazvy = [l.strip() for l in result.stdout.split('\n') 
                            if l.strip() and l.strip() != 'Name']
            except FileNotFoundError:
                # Fallback: PowerShell (Windows 11)
                result = subprocess.run(
                    ['powershell', '-Command',
                     'Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name'],
                    capture_output=True, text=True, timeout=10
                )
                gpu_nazvy = [l.strip() for l in result.stdout.split('\n') if l.strip()]
        
        elif system == 'Linux':
            try:
                result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
                for line in result.stdout.split('\n'):
                    if any(x in line for x in ['VGA', '3D controller', 'Display']):
                        if ':' in line:
                            nazev = line.split(':', 2)[-1].strip()
                            gpu_nazvy.append(nazev)
            except FileNotFoundError:
                pass
        
        if gpu_nazvy:
            nazev = " / ".join(gpu_nazvy)
            ma_cuda = 'nvidia' in nazev.lower() or 'geforce' in nazev.lower()
            
            # DOPORUCENI
            if ma_cuda:
                doporuceni = "NVIDIA GPU detekovana. Pro GPU akceleraci muzes pouzit Ollamu nebo zkompilovat llama-cpp s CUDA."
            else:
                doporuceni = "Pro GPU akceleraci na AMD/Intel nainstaluj Ollamu (ollama.com). Tvuj projekt ji automaticky vyuzije."
            
            return jsonify({
                'dostupna': True,
                'vram_gb': 0,
                'nazev': nazev,
                'cuda': ma_cuda,
                'doporuceni': doporuceni
            })
    except Exception as e:
        print(f"Chyba detekce GPU: {e}")
    
    return jsonify({'dostupna': False, 'vram_gb': 0, 'nazev': 'Žádná GPU', 'cuda': False})