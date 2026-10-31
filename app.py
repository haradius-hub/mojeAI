# app.py
import os
import json
import glob
import re
import hashlib
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import chromadb
from chromadb.utils import embedding_functions
import requests
import time

app = Flask(__name__)
CORS(app)

# ============ NASTAVENÍ ============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PAMET_DIR = os.path.join(BASE_DIR, "pamet")
API_KLICE_DIR = os.path.join(BASE_DIR, "api_klic")
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELY_DIR = os.path.join(BASE_DIR, "modely")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

os.makedirs(PAMET_DIR, exist_ok=True)
os.makedirs(API_KLICE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODELY_DIR, exist_ok=True)

# ============ KONFIGURACE ============
def nacti_konfiguraci():
    """Načte konfiguraci z config.json, nebo vytvoří výchozí"""
    vychozi = {
        "system_prompt": "Jsi užitečný asistent. Odpovídej česky, stručně a výstižně. Používej přirozenou češtinu bez zbytečných formalit.",
        "vychozi_model": "gemini",
        "pristupne_slozky": [],
        "internet": False,
        "max_vzpominek": 5,
        "pocet_souboru_ze_slozky": 10,
        "pouzit_gpu": False,
        "gpu_vrstev": 25
    }
    
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            for key, value in vychozi.items():
                if key not in config:
                    config[key] = value
            return config
    else:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(vychozi, f, indent=2, ensure_ascii=False)
        return vychozi

def uloz_konfiguraci(config):
    """Uloží konfiguraci"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

config = nacti_konfiguraci()

# ============ VEKTOROVÁ PAMĚŤ ============
# Embedding model - používáme model ze složky modely/
embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=os.path.join(BASE_DIR, "modely", "all-MiniLM-L6-v2")
)

chroma_client = chromadb.PersistentClient(path=os.path.join(DATA_DIR, "chroma_db"))
kolekce = chroma_client.get_or_create_collection(
    name="pamet",
    embedding_function=embedder
)

# ============ FUNKCE PRO PAMĚŤ ============
def uloz_do_pameti(text, zdroj="chat", metadata=None):
    """Uloží text do paměti (soubor i vektorová DB)"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    hash_id = hashlib.md5(f"{timestamp}{text[:50]}".encode()).hexdigest()[:12]
    
    soubor = os.path.join(PAMET_DIR, f"{timestamp}_{hash_id}.txt")
    with open(soubor, "w", encoding="utf-8") as f:
        f.write(text)
    
    meta = {"zdroj": zdroj, "cas": timestamp}
    if metadata:
        meta.update(metadata)
    
    kolekce.add(
        documents=[text],
        metadatas=[meta],
        ids=[f"id_{timestamp}_{hash_id}"]
    )
    return True

def najdi_v_pameti(dotaz, pocet=5):
    """Najde nejrelevantnější vzpomínky k dotazu"""
    try:
        vysledky = kolekce.query(query_texts=[dotaz], n_results=pocet)
        if vysledky and vysledky['documents'] and len(vysledky['documents']) > 0:
            return vysledky['documents'][0]
    except Exception:
        pass
    return []

def indexuj_slozku(cesta):
    """Projde složku a uloží všechny textové soubory do paměti"""
    if not os.path.exists(cesta):
        return {"status": "error", "zprava": f"Složka {cesta} neexistuje"}
    
    podporovane = ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.csv']
    nacteno = 0
    chyby = []
    
    for root, dirs, files in os.walk(cesta):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in podporovane:
                try:
                    cesta_souboru = os.path.join(root, file)
                    with open(cesta_souboru, 'r', encoding='utf-8', errors='ignore') as f:
                        obsah = f.read()
                    if len(obsah) > 10000:
                        obsah = obsah[:10000] + f"\n... (soubor zkrácen, původní délka {len(obsah)} znaků)"
                    
                    relativni = os.path.relpath(cesta_souboru, cesta)
                    uloz_do_pameti(
                        f"SOUBOR: {relativni}\n{obsah}",
                        zdroj="slozka",
                        metadata={"soubor": file, "cesta": cesta_souboru}
                    )
                    nacteno += 1
                except Exception as e:
                    chyby.append(f"{file}: {str(e)}")
    
    return {
        "status": "ok",
        "zprava": f"Načteno {nacteno} souborů",
        "nacteno": nacteno,
        "chyby": chyby
    }

# ============ FUNKCE PRO MODEL ============
def ziskej_dostupne_modele():
    """Zjistí, které API klíče jsou k dispozici + lokální modely"""
    dostupne = []
    
    # 1. API klíče
    for soubor in os.listdir(API_KLICE_DIR):
        if soubor.endswith('.txt'):
            provider = soubor.replace('.txt', '')
            cesta = os.path.join(API_KLICE_DIR, soubor)
            with open(cesta, 'r', encoding='utf-8') as f:
                klic = f.read().strip()
                if klic and len(klic) > 5:
                    dostupne.append(provider)
    
    # 2. Lokální modely ze složky modely/
    lokalni_modely = ziskej_dostupne_lokalni_modely()
    for model in lokalni_modely:
        # Vytvoříme unikátní identifikátor
        dostupne.append({
            'id': f"lokalni_{model['id']}",
            'nazev': model['zobrazovany_nazev'],
            'typ': 'lokalni',
            'info': model
        })
    
    # 3. Ollama (původní lokální)
    try:
        r = requests.get('http://localhost:11434/api/tags', timeout=2)
        if r.status_code == 200:
            dostupne.append({
                'id': 'ollama',
                'nazev': '🦙 Ollama (llama3.2)',
                'typ': 'ollama',
                'info': None
            })
    except:
        pass
    
    return dostupne

def nacti_api_klic(provider):
    """Načte API klíč ze souboru"""
    soubor = os.path.join(API_KLICE_DIR, f"{provider}.txt")
    if os.path.exists(soubor):
        with open(soubor, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

# ============ PRÁCE S LOKÁLNÍMI MODELY ZE SLOŽKY ============
def ziskej_dostupne_lokalni_modely():
    """Zjistí, jaké lokální modely jsou ve složce modely/"""
    dostupne = []
    counter = 1
    
    # 1. GGUF modely (.gguf)
    for root, dirs, files in os.walk(MODELY_DIR):
        for file in files:
            if file.endswith('.gguf'):
                # Přeskočíme vision encoder
                if 'mmproj' in file.lower():
                    continue
                cesta = os.path.join(root, file)
                nazev_slozky = os.path.basename(root)
                # Zjistíme velikost v GB
                velikost = os.path.getsize(cesta) / (1024**3)
                # Vytvoříme zobrazovací název s velikostí
                zobrazovany_nazev = f"{nazev_slozky} [{velikost:.2f} GB]"
                
                dostupne.append({
                    'id': f"gguf_{counter}",
                    'cesta': cesta,
                    'typ': 'gguf',
                    'nazev': nazev_slozky,
                    'soubor': file,
                    'velikost_gb': round(velikost, 2),
                    'zobrazovany_nazev': zobrazovany_nazev
                })
                counter += 1
    
    # 2. Transformers modely
    for polozka in os.listdir(MODELY_DIR):
        cesta = os.path.join(MODELY_DIR, polozka)
        if os.path.isdir(cesta):
            # Přeskočíme, pokud už máme GGUF ve stejné složce
            if any(m['nazev'] == polozka for m in dostupne):
                continue
            ma_config = os.path.exists(os.path.join(cesta, "config.json"))
            ma_vahy = os.path.exists(os.path.join(cesta, "model.safetensors")) or \
                      os.path.exists(os.path.join(cesta, "pytorch_model.bin"))
            if ma_config and ma_vahy:
                dostupne.append({
                    'id': f"trans_{counter}",
                    'cesta': cesta,
                    'typ': 'transformers',
                    'nazev': polozka,
                    'soubor': '',
                    'velikost_gb': 0,
                    'zobrazovany_nazev': f"{polozka} (Transformers)"
                })
                counter += 1
    
    return dostupne

def spocitej_optimalni_vrstvy(model_path, vram_gb):
    """Spočítá optimální počet vrstev na GPU podle velikosti modelu"""
    try:
        velikost_mb = os.path.getsize(model_path) / (1024**2)
        velikost_gb = velikost_mb / 1024
        
        if 'gemma' in model_path.lower() or '12b' in model_path.lower():
            celkem_vrstev = 42
        elif 'phi' in model_path.lower():
            celkem_vrstev = 32
        else:
            celkem_vrstev = 40
        
        if velikost_gb > 0 and vram_gb > 0:
            vrstva_gb = velikost_gb / celkem_vrstev
            max_vrstev = int(vram_gb / vrstva_gb)
            return min(celkem_vrstev, max(0, max_vrstev - 2))
    except:
        pass
    return 20

def zjisti_dostupnou_gpu():
    """Zjistí, zda je dostupná GPU a kolik má VRAM"""
    try:
        import torch
        if torch.cuda.is_available():
            vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            return {
                'dostupna': True,
                'vram_gb': round(vram, 1),
                'nazev': torch.cuda.get_device_name(0)
            }
    except:
        pass
    
    try:
        from llama_cpp import Llama
        import subprocess
        result = subprocess.run(['python', '-c', 'import llama_cpp; print(llama_cpp.llama_supports_gpu())'], 
                               capture_output=True, text=True, timeout=5)
        if 'True' in result.stdout:
            return {'dostupna': True, 'vram_gb': 0, 'nazev': 'GPU (llama-cpp-python s CUDA)'}
    except:
        pass
    
    return {'dostupna': False, 'vram_gb': 0, 'nazev': 'Žádná GPU'}

def odpoved_lokalni_gguf(prompt, model_path):
    """Odpověď přes GGUF model s podporou GPU"""
    try:
        from llama_cpp import Llama
        
        pouzit_gpu = config.get('pouzit_gpu', False)
        gpu_vrstev = config.get('gpu_vrstev', 25)
        gpu_info = zjisti_dostupnou_gpu()
        
        if pouzit_gpu and not gpu_info['dostupna']:
            return "⚠️ GPU je povolena v nastavení, ale nebyla detekována. Model poběží na CPU."
        
        # Nastavíme parametry
        if pouzit_gpu and gpu_info['dostupna']:
            if gpu_info['vram_gb'] > 0 and gpu_info['vram_gb'] < 6:
                optimalni = spocitej_optimalni_vrstvy(model_path, gpu_info['vram_gb'])
                n_gpu_layers = min(gpu_vrstev, optimalni)
                if n_gpu_layers < 5:
                    return f"⚠️ GPU má jen {gpu_info['vram_gb']} GB VRAM, pro tento model málo. Doporučujeme vypnout GPU v nastavení."
            else:
                n_gpu_layers = gpu_vrstev if gpu_vrstev > 0 else -1
        else:
            n_gpu_layers = 0
        
        llm = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_threads=4,
            n_gpu_layers=n_gpu_layers,
            verbose=False
        )
        
        response = llm(
            prompt,
            max_tokens=2048,
            temperature=0.7,
            echo=False
        )
        return response['choices'][0]['text']
        
    except ImportError:
        return "❌ Chybí knihovna llama-cpp-python. Nainstaluj: pip install llama-cpp-python"
    except Exception as e:
        return f"❌ Chyba GGUF: {str(e)}"

def odpoved_lokalni_transformers(prompt, model_dir):
    """Odpověď přes Transformers model (vyžaduje torch a transformers)"""
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch
        
        tokenizer = AutoTokenizer.from_pretrained(model_dir)
        model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None
        )
        
        inputs = tokenizer(prompt, return_tensors="pt")
        if not torch.cuda.is_available():
            inputs = {k: v.to('cpu') for k, v in inputs.items()}
            model = model.to('cpu')
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=2048,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        if response.startswith(prompt):
            response = response[len(prompt):].strip()
        return response
    except ImportError as e:
        return f"❌ Chybí knihovna. Nainstaluj: pip install torch transformers"
    except Exception as e:
        return f"❌ Chyba Transformers: {str(e)}"

def odpoved_lokalni_ollama(prompt, model_name="llama3.2"):
    """Odpověď přes Ollama API"""
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': model_name,
                'prompt': prompt,
                'stream': False
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json()['response']
        else:
            return f"❌ Chyba Ollamy: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return "❌ Ollama není spuštěná. Spusť 'ollama serve'"
    except Exception as e:
        return f"❌ Chyba: {str(e)}"

def odpoved_lokalni(prompt, model_name="llama3.2", model_info=None):
    """
    Hlavní funkce pro lokální odpovědi.
    - Pokud je zadán model_info, použije se GGUF nebo Transformers ze složky modely/
    - Jinak se použije Ollama
    """
    if model_info:
        typ = model_info.get('typ')
        cesta = model_info.get('cesta')
        
        if typ == 'gguf':
            return odpoved_lokalni_gguf(prompt, cesta)
        elif typ == 'transformers':
            return odpoved_lokalni_transformers(prompt, cesta)
        else:
            return f"Neznámý typ modelu: {typ}"
    
    return odpoved_lokalni_ollama(prompt, model_name)

# ============ JEDNOTLIVÍ POSKYTOVATELÉ ============
def odpoved_gemini(prompt):
    api_klic = nacti_api_klic("gemini")
    if not api_klic:
        return "❌ Chybí API klíč pro Gemini. Vlož ho do api_klic/gemini.txt"
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_klic)
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Chyba Gemini: {str(e)}"

def odpoved_deepseek(prompt):
    api_klic = nacti_api_klic("deepseek")
    if not api_klic:
        return "❌ Chybí API klíč pro DeepSeek. Vlož ho do api_klic/deepseek.txt"
    try:
        response = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_klic}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'deepseek-chat',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 2048
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"❌ DeepSeek error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"❌ Chyba DeepSeek: {str(e)}"

def odpoved_openai(prompt):
    api_klic = nacti_api_klic("openai")
    if not api_klic:
        return "❌ Chybí API klíč pro OpenAI. Vlož ho do api_klic/openai.txt"
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_klic)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=2048
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Chyba OpenAI: {str(e)}"

def odpoved_claude(prompt):
    api_klic = nacti_api_klic("claude")
    if not api_klic:
        return "❌ Chybí API klíč pro Claude. Vlož ho do api_klic/claude.txt"
    try:
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': api_klic,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            },
            json={
                'model': 'claude-3-haiku-20240307',
                'max_tokens': 2048,
                'messages': [{'role': 'user', 'content': prompt}]
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()['content'][0]['text']
        else:
            return f"❌ Claude error: {response.status_code}"
    except Exception as e:
        return f"❌ Chyba Claude: {str(e)}"

# ============ ODPOVĚD S PAMĚTÍ ============
def odpoved_s_pameti(dotaz, provider="gemini", lokalni_model="llama3.2", lokalni_model_info=None):
    """Vygeneruje odpověď s využitím paměti"""
    
    # 1. Najdeme relevantní vzpomínky
    vzpominky = najdi_v_pameti(dotaz, pocet=config.get("max_vzpominek", 5))
    kontext = "\n".join(vzpominky) if vzpominky else "Žádné relevantní vzpomínky."
    
    # 2. Sestavíme prompt
    system_prompt = config.get("system_prompt", "Jsi užitečný asistent. Odpovídej česky.")
    
    # 3. Přidáme informace z připojených složek
    slozky_info = ""
    if config.get("pristupne_slozky"):
        slozky_info = "\n\nPŘÍSTUPNÉ SLOŽKY:\n"
        for slozka in config["pristupne_slozky"]:
            if os.path.exists(slozka):
                soubory = glob.glob(os.path.join(slozka, "**/*"), recursive=True)
                pocet = len([f for f in soubory if os.path.isfile(f)])
                slozky_info += f"- {slozka} ({pocet} souborů)\n"
    
    # 4. Přidáme možnost internetu
    internet_info = ""
    if config.get("internet", False):
        internet_info = "\n\nPokud potřebuješ aktuální informace, můžeš provést vyhledávání na internetu."
    
    # 5. Sestavíme kompletní prompt
    prompt = f"""{system_prompt}

PAMĚŤ (předchozí konverzace a poznámky):
{kontext}
{slozky_info}
{internet_info}

OTÁZKA: {dotaz}

ODPOVĚĎ:"""
    
    # 6. Vybereme model
    if provider == "lokalni":
        return odpoved_lokalni(prompt, lokalni_model, lokalni_model_info)
    elif provider == "ollama":
        return odpoved_lokalni_ollama(prompt, lokalni_model)
    elif provider == "gemini":
        return odpoved_gemini(prompt)
    elif provider == "deepseek":
        return odpoved_deepseek(prompt)
    elif provider == "openai":
        return odpoved_openai(prompt)
    elif provider == "claude":
        return odpoved_claude(prompt)
    else:
        return f"Neznámý model: {provider}"

# ============ INTERNETOVÉ VYHLEDÁVÁNÍ ============
def hledej_na_internetu(dotaz):
    """Jednoduché vyhledávání přes DuckDuckGo"""
    try:
        response = requests.get(
            'https://api.duckduckgo.com/',
            params={
                'q': dotaz,
                'format': 'json',
                'no_html': 1,
                'skip_disambig': 1
            },
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            vysledky = []
            if data.get('Abstract'):
                vysledky.append(data['Abstract'])
            if data.get('RelatedTopics'):
                for topic in data['RelatedTopics'][:3]:
                    if topic.get('Text'):
                        vysledky.append(topic['Text'])
            return "\n".join(vysledky) if vysledky else "Nenalezeny žádné výsledky."
        return "Vyhledávání selhalo."
    except Exception as e:
        return f"Chyba vyhledávání: {str(e)}"

# ============ WEBOVÉ ROZHRANÍ ============
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    """Vrátí aktuální konfiguraci a dostupné modely"""
    return jsonify({
        'config': config,
        'dostupne_modele': ziskej_dostupne_modele(),
        'vychozi': config.get('vychozi_model', 'gemini')
    })

@app.route('/api/config', methods=['POST'])
def set_config():
    """Uloží konfiguraci"""
    data = request.json
    for key, value in data.items():
        if key in config:
            config[key] = value
    uloz_konfiguraci(config)
    return jsonify({'status': 'ok', 'config': config})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    dotaz = data.get('dotaz', '')
    model_id = data.get('model', config.get('vychozi_model', 'gemini'))
    lokalni_model_info = data.get('lokalni_model_info')
    
    if not dotaz:
        return jsonify({'odpoved': 'Prosím napiš otázku.'})
    
    # Zkontrolujeme, zda má uživatel povolený internet
    if config.get('internet', False):
        internetova_slova = ['dnes', 'aktuální', 'nový', 'zpráva', 'dneska', 'včera', 'zítra', 'počasí', 'cena', 'kurz']
        if any(slovo in dotaz.lower() for slovo in internetova_slova):
            internet_info = hledej_na_internetu(dotaz)
            uloz_do_pameti(f"Internetové vyhledávání: {dotaz}\nVýsledek: {internet_info}", zdroj="internet")
    
    # Uložíme dotaz do paměti
    uloz_do_pameti(f"Otázka: {dotaz}", zdroj="dotaz")
    
    # Získáme odpověď - pokud je model_id "lokalni", použijeme lokalni_model_info
    if model_id == 'lokalni' and lokalni_model_info:
        odpoved = odpoved_s_pameti(dotaz, 'lokalni', lokalni_model="llama3.2", lokalni_model_info=lokalni_model_info)
    else:
        odpoved = odpoved_s_pameti(dotaz, model_id)
    
    # Uložíme odpověď do paměti
    uloz_do_pameti(f"Odpověď: {odpoved}", zdroj="odpoved")
    
    return jsonify({'odpoved': odpoved})

@app.route('/api/pamet', methods=['GET'])
def zobraz_pamet():
    """Zobrazí uložené vzpomínky"""
    soubory = sorted(glob.glob(os.path.join(PAMET_DIR, "*.txt")), reverse=True)
    obsah = []
    for soubor in soubory[:30]:
        try:
            with open(soubor, "r", encoding="utf-8") as f:
                text = f.read()
                obsah.append({
                    'soubor': os.path.basename(soubor),
                    'obsah': text[:300] + "..." if len(text) > 300 else text,
                    'delka': len(text)
                })
        except:
            pass
    return jsonify(obsah)

@app.route('/api/slozka', methods=['POST'])
def pridat_slozku():
    """Přidá složku k indexování"""
    data = request.json
    cesta = data.get('cesta', '').strip()
    
    if not cesta or not os.path.exists(cesta):
        return jsonify({'status': 'error', 'zprava': 'Složka neexistuje'})
    
    if cesta not in config['pristupne_slozky']:
        config['pristupne_slozky'].append(cesta)
        uloz_konfiguraci(config)
    
    vysledek = indexuj_slozku(cesta)
    return jsonify(vysledek)

@app.route('/api/slozky', methods=['GET'])
def zobraz_slozky():
    """Zobrazí připojené složky"""
    slozky = []
    for cesta in config.get('pristupne_slozky', []):
        if os.path.exists(cesta):
            pocet = len(glob.glob(os.path.join(cesta, "**/*"), recursive=True))
            slozky.append({'cesta': cesta, 'pocet': pocet})
        else:
            slozky.append({'cesta': cesta, 'pocet': 0, 'chybi': True})
    return jsonify(slozky)

@app.route('/api/slozka', methods=['DELETE'])
def odebrat_slozku():
    """Odebere složku z přístupných"""
    data = request.json
    cesta = data.get('cesta', '').strip()
    if cesta in config['pristupne_slozky']:
        config['pristupne_slozky'].remove(cesta)
        uloz_konfiguraci(config)
        return jsonify({'status': 'ok'})
    return jsonify({'status': 'error', 'zprava': 'Složka nenalezena'})

@app.route('/api/prompt', methods=['POST'])
def nastav_prompt():
    """Nastaví systémový prompt"""
    data = request.json
    prompt = data.get('prompt', '').strip()
    if prompt:
        config['system_prompt'] = prompt
        uloz_konfiguraci(config)
        return jsonify({'status': 'ok'})
    return jsonify({'status': 'error', 'zprava': 'Prázdný prompt'})

@app.route('/api/lokalni-modely', methods=['GET'])
def get_lokalni_modely():
    """Vrátí seznam dostupných lokálních modelů ze složky modely/"""
    return jsonify(ziskej_dostupne_lokalni_modely())

@app.route('/api/gpu-info', methods=['GET'])
def get_gpu_info():
    """Vrátí informace o dostupné GPU"""
    info = zjisti_dostupnou_gpu()
    return jsonify(info)

# ============ SPUŠTĚNÍ ============
if __name__ == '__main__':
    print("=" * 60)
    print("🤖 MojeAI - Portabilní asistent s pamětí")
    print("=" * 60)
    print(f"📂 Aplikace: {BASE_DIR}")
    print(f"🧠 Paměť: {PAMET_DIR}")
    print(f"🔑 API klíče: {API_KLICE_DIR}")
    print(f"📁 Modely: {MODELY_DIR}")
    print("=" * 60)
    print("🌐 Otevři v prohlížeči: http://localhost:5000")
    print("=" * 60)
    app.run(debug=False, host='0.0.0.0', port=5000)