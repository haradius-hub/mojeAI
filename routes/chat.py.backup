# routes/chat.py
from flask import Blueprint, request, jsonify
from config import Config
from core.memory import memory_manager
from core.providers import Providers
from datetime import datetime
import requests
import os
import tempfile
import json
from ddgs import DDGS

chat_bp = Blueprint('chat', __name__)

def hledej_na_internetu(dotaz):
    dotaz_lower = dotaz.lower()
    
    if any(x in dotaz_lower for x in ['pocasi', 'počasí', 'teplota']) \
       and not any(x in dotaz_lower for x in ['kde jsi', 'odkud', 'zdroj', 'odkaz']):
        try:
            mesta = ['praha', 'brno', 'ostrava', 'plzen', 'plzeň', 'liberec', 'olomouc', 
                     'české budějovice', 'ceske budejovice', 'hradec králové', 'hradec kralove',
                     'pardubice', 'zlin', 'zlín', 'jihlava', 'karlovy vary', 'usti', 'ústí']
            mesto = 'praha'
            for m in mesta:
                if m in dotaz_lower:
                    mesto = m
                    break
            
            geo = requests.get('https://geocoding-api.open-meteo.com/v1/search', params={'name': mesto, 'count': 1, 'language': 'cs'}, timeout=10).json()
            if not geo.get('results'): return f"Nepodařilo se najít město {mesto}."
            
            lat = geo['results'][0]['latitude']
            lon = geo['results'][0]['longitude']
            nazev_mesta = geo['results'][0]['name']
            
            weather = requests.get('https://api.open-meteo.com/v1/forecast', params={'latitude': lat, 'longitude': lon, 'current': 'temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m', 'timezone': 'Europe/Prague'}, timeout=10).json()
            cur = weather.get('current', {})
            
            kody = {0: 'jasno', 1: 'převážně jasno', 2: 'polojasno', 3: 'zataženo', 45: 'mlha', 51: 'slabé mrholení', 61: 'déšť', 63: 'střední déšť', 71: 'slabé sněžení', 80: 'přeháňky', 95: 'bouřka'}
            pocasi_text = kody.get(cur.get('weather_code'), 'neznámé')
            
            return (f"Aktuální počasí v {nazev_mesta}: {pocasi_text}, teplota {cur.get('temperature_2m', '?')}°C, vlhkost {cur.get('relative_humidity_2m', '?')}%, vítr {cur.get('wind_speed_10m', '?')} km/h.")
        except Exception as e:
            return f"Chyba při zjišťování počasí: {e}"
    
    try:
        with DDGS() as ddgs:
            vysledky = [f"- {r['title']}: {r['body']}" for r in ddgs.text(dotaz, max_results=3)]
            if vysledky: return "\n".join(vysledky)
    except Exception as e:
        print(f"DDG chyba: {e}")
    
    try:
        response = requests.get('https://api.duckduckgo.com/', params={'q': dotaz, 'format': 'json', 'no_html': 1, 'skip_disambig': 1}, timeout=10).json()
        vysledky = []
        if response.get('Abstract'): vysledky.append(response['Abstract'])
        for topic in response.get('RelatedTopics', [])[:3]:
            if isinstance(topic, dict) and topic.get('Text'): vysledky.append(topic['Text'])
        if vysledky: return "\n".join(vysledky)
    except Exception as e:
        pass
    
    return "Nenalezeny zadne relevantni vysledky."

@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    # Zjistíme, zda jde o multipart (soubor) nebo JSON
    if request.content_type and 'multipart/form-data' in request.content_type:
        dotaz = request.form.get('dotaz', '')
        model_id = request.form.get('model', 'gemini')
        force_search = request.form.get('force_search') == 'true'
        model_info_str = request.form.get('lokalni_model_info')
        model_info = json.loads(model_info_str) if model_info_str else None
        nahrany_soubor = request.files.get('file')
    else:
        data = request.json
        dotaz = data.get('dotaz', '')
        model_id = data.get('model', 'gemini')
        force_search = data.get('force_search', False)
        model_info = data.get('lokalni_model_info')
        nahrany_soubor = None

    if not dotaz and not nahrany_soubor:
        return jsonify({'odpoved': 'Prosim napis otazku nebo nahraj soubor.'})

    text_ze_souboru = ""
    if nahrany_soubor:
        temp_dir = tempfile.gettempdir()
        cesta = os.path.join(temp_dir, nahrany_soubor.filename)
        nahrany_soubor.save(cesta)
        try:
            if cesta.lower().endswith('.pdf'):
                from pypdf import PdfReader
                reader = PdfReader(cesta)
                text_ze_souboru = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
            elif cesta.lower().endswith(('.txt', '.md', '.py', '.csv')):
                with open(cesta, 'r', encoding='utf-8') as f:
                    text_ze_souboru = f.read()
            else:
                text_ze_souboru = f"[Soubor {nahrany_soubor.filename} byl nahrán, ale textovou extrakci pro tento formát zatím neumím.]"
        except Exception as e:
            text_ze_souboru = f"[Chyba při čtení souboru: {e}]"
        finally:
            if os.path.exists(cesta): os.remove(cesta)

    config = Config.nacti()
    ted = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    internet_info = ""
    slova_pro_hledani = ['pocasi', 'počasí', 'teplota', 'novinky', 'zpravy', 'zprávy', 'dnes', 'aktualni', 'aktuální']
    chce_hledat = force_search or (config.get('internet', False) and any(s in dotaz.lower() for s in slova_pro_hledani))
    
    if chce_hledat:
        print(f"[INFO] Vyhledavam na internetu: {dotaz}")
        vysledky = hledej_na_internetu(dotaz)
        internet_info = f"\nDŮLEŽITÉ: Níže jsou výsledky vyhledávání na internetu. POUŽIJ JE ve své odpovědi.\nVÝSLEDKY Z INTERNETU:\n{vysledky}\n"
        memory_manager.uloz(f"Internetove vyhledavani: {dotaz}\nVysledek: {vysledky}", zdroj="internet")

    vzpominky = memory_manager.hledej(dotaz, pocet=config.get("max_vzpominek", 5))
    kontext = "\n".join(vzpominky) if vzpominky else "Zadne relevantni vzpominky."
    
    soubor_info = f"\nOBSAH NAHRANÉHO SOUBORU:\n{text_ze_souboru}\n" if text_ze_souboru else ""

    prompt = f"""{config.get('system_prompt')}
Aktualni datum a cas: {ted}
PAMET:
{kontext}
{internet_info}
{soubor_info}
OTAZKA: {dotaz}
ODPOVED:"""
    
    memory_manager.uloz(f"Otazka: {dotaz}", zdroj="dotaz")
    odpoved = Providers.generuj(prompt, model_id, model_info)
    memory_manager.uloz(f"Odpoved: {odpoved}", zdroj="odpoved")
    
    return jsonify({'odpoved': odpoved})