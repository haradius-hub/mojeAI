# routes/memory.py
import os
import glob
from flask import Blueprint, request, jsonify
from config import Config
from core.memory import memory_manager

memory_bp = Blueprint('memory', __name__)

@memory_bp.route('/api/pamet', methods=['GET'])
def zobraz_pamet():
    return jsonify(memory_manager.ziskej_posledni(30))

@memory_bp.route('/api/slozky', methods=['GET'])
def zobraz_slozky():
    config = Config.nacti()
    slozky = []
    for cesta in config.get('pristupne_slozky', []):
        if os.path.exists(cesta):
            pocet = len(glob.glob(os.path.join(cesta, "**/*"), recursive=True))
            slozky.append({'cesta': cesta, 'pocet': pocet})
        else:
            slozky.append({'cesta': cesta, 'pocet': 0, 'chybi': True})
    return jsonify(slozky)

@memory_bp.route('/api/slozka', methods=['POST'])
def pridat_slozku():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get('cesta'), str):
        return jsonify({'status': 'error', 'zprava': 'Neplatná cesta ke složce.'}), 400
    vstupni_cesta = data['cesta'].strip()
    if not vstupni_cesta:
        return jsonify({'status': 'error', 'zprava': 'Zadej cestu ke složce.'}), 400
    cesta = os.path.realpath(vstupni_cesta)
    if not os.path.isdir(cesta):
        return jsonify({'status': 'error', 'zprava': 'Složka neexistuje nebo nejde o adresář.'}), 400
    
    config = Config.nacti()
    if cesta not in config['pristupne_slozky']:
        config['pristupne_slozky'].append(cesta)
        Config.uloz(config)
    
    # Zjednodušená indexace pro ukázku
    return jsonify({'status': 'ok', 'zprava': 'Složka přidána (indexace přesunuta)'})

@memory_bp.route('/api/slozka', methods=['DELETE'])
def odebrat_slozku():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get('cesta'), str):
        return jsonify({'status': 'error', 'zprava': 'Neplatná cesta ke složce.'}), 400
    vstupni_cesta = data['cesta'].strip()
    if not vstupni_cesta:
        return jsonify({'status': 'error', 'zprava': 'Zadej cestu ke složce.'}), 400
    cesta = os.path.realpath(vstupni_cesta)
    config = Config.nacti()
    for ulozena_cesta in (vstupni_cesta, cesta):
        if ulozena_cesta in config['pristupne_slozky']:
            config['pristupne_slozky'].remove(ulozena_cesta)
            Config.uloz(config)
            return jsonify({'status': 'ok'})
    return jsonify({'status': 'error', 'zprava': 'Nenalezeno'})
