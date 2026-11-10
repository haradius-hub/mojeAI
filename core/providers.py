# core/providers.py
import os
import requests
from config import Config

class Providers:
    POVOLENI_POSKYTOVATELE = {'gemini', 'deepseek', 'openai', 'claude'}

    @staticmethod
    def nacti_klic(provider):
        if provider not in Providers.POVOLENI_POSKYTOVATELE:
            return None
        cesta = os.path.join(Config.API_KLICE_DIR, f"{provider}.txt")
        if os.path.exists(cesta):
            with open(cesta, "r", encoding="utf-8") as f:
                return f.read().strip()
        return None

    @staticmethod
    def uloz_klic(provider, klic):
        if provider not in Providers.POVOLENI_POSKYTOVATELE:
            raise ValueError('Nepovolený poskytovatel API.')
        if not isinstance(klic, str) or not klic.strip() or len(klic) > 4096:
            raise ValueError('Neplatný API klíč.')
        cesta = os.path.join(Config.API_KLICE_DIR, f"{provider}.txt")
        docasna = cesta + '.tmp'
        fd = os.open(docasna, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(klic.strip())
            os.replace(docasna, cesta)
            try:
                os.chmod(cesta, 0o600)
            except OSError:
                pass
        finally:
            if os.path.exists(docasna):
                os.remove(docasna)
        return True

    @staticmethod
    def dostupne_modely():
        dostupne = []
        # 1. Cloudove API
        for provider in sorted(Providers.POVOLENI_POSKYTOVATELE):
            dostupne.append({
                'id': provider,
                'nazev': provider.capitalize(),
                'typ': 'api',
                'ma_klic': bool(Providers.nacti_klic(provider))
            })
        
        # 2. Lokalni GGUF modely
        for root, dirs, files in os.walk(Config.MODELY_DIR):
            for file in files:
                if file.endswith('.gguf') and 'mmproj' not in file.lower():
                    cesta = os.path.join(root, file)
                    nazev = os.path.basename(root)
                    velikost = os.path.getsize(cesta) / (1024**3)
                    dostupne.append({
                        'id': f"lokalni_{nazev}",
                        'nazev': f"{nazev} [{velikost:.2f} GB]",
                        'typ': 'lokalni',
                        'info': {'cesta': cesta, 'typ': 'gguf'}
                    })
        
        # 3. Ollama modely (pokud bezi)
        try:
            r = requests.get('http://localhost:11434/api/tags', timeout=1)
            if r.status_code == 200:
                for model in r.json().get('models', []):
                    nazev = model['name']
                    dostupne.append({
                        'id': f"ollama/{nazev}",
                        'nazev': f"🦙 {nazev} (Ollama)",
                        'typ': 'ollama'
                    })
        except Exception:
            pass
            
        return dostupne

    @staticmethod
    def odpoved_gemini(prompt):
        klic = Providers.nacti_klic("gemini")
        if not klic: return "❌ Chybí Gemini klíč."
        try:
            import google.generativeai as genai
            genai.configure(api_key=klic)
            model = genai.GenerativeModel('gemini-2.0-flash')
            return model.generate_content(prompt).text
        except Exception as e:
            return f"❌ Chyba Gemini: {str(e)}"

    @staticmethod
    def odpoved_deepseek(prompt):
        klic = Providers.nacti_klic("deepseek")
        if not klic: return "❌ Chybí DeepSeek klíč."
        try:
            r = requests.post('https://api.deepseek.com/v1/chat/completions',
                headers={'Authorization': f'Bearer {klic}'},
                json={'model': 'deepseek-chat', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 2048},
                timeout=30)
            return r.json()['choices'][0]['message']['content'] if r.status_code == 200 else f"❌ Chyba: {r.status_code}"
        except Exception as e:
            return f"❌ Chyba DeepSeek: {str(e)}"

    @staticmethod
    def odpoved_openai(prompt):
        klic = Providers.nacti_klic("openai")
        if not klic: return "❌ Chybí OpenAI klíč."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=klic)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{'role': 'user', 'content': prompt}],
                max_tokens=2048
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ Chyba OpenAI: {str(e)}"

    @staticmethod
    def odpoved_claude(prompt):
        klic = Providers.nacti_klic("claude")
        if not klic: return "❌ Chybí Claude klíč."
        try:
            r = requests.post('https://api.anthropic.com/v1/messages',
                headers={'x-api-key': klic, 'anthropic-version': '2023-06-01'},
                json={'model': 'claude-3-haiku-20240307', 'max_tokens': 2048, 'messages': [{'role': 'user', 'content': prompt}]},
                timeout=30)
            return r.json()['content'][0]['text'] if r.status_code == 200 else f"❌ Chyba: {r.status_code}"
        except Exception as e:
            return f"❌ Chyba Claude: {str(e)}"

    @staticmethod
    def odpoved_ollama(prompt, model_name):
        try:
            r = requests.post('http://localhost:11434/api/generate',
                json={'model': model_name, 'prompt': prompt, 'stream': False},
                timeout=120)
            return r.json()['response'] if r.status_code == 200 else f"❌ Chyba Ollama: {r.status_code}"
        except Exception as e:
            return f"❌ Chyba Ollama: {str(e)}"

    @staticmethod
    def odpoved_gguf(prompt, cesta):
        try:
            from llama_cpp import Llama
            from config import Config
            
            config = Config.nacti()
            n_ctx = config.get('n_ctx', 4096)
            n_threads = config.get('n_threads', 8)
            
            llm = Llama(
                model_path=cesta, 
                n_ctx=n_ctx, 
                n_threads=n_threads, 
                n_gpu_layers=0, 
                verbose=False
            )
            
            # Zkusíme zjistit, jaký chat formát model používá
            # Pro Gemma-3 (a OpenEuroLLM) použijeme "gemma"
            # Pro ostatní necháme výchozí (raw completion)
            chat_format = None
            nazev_lower = cesta.lower()
            if 'gemma' in nazev_lower or 'euro' in nazev_lower:
                chat_format = "gemma"
            elif 'qwen' in nazev_lower:
                chat_format = "chatml"  # Qwen používá ChatML
            elif 'phi' in nazev_lower:
                chat_format = "chatml"
            elif 'llama' in nazev_lower:
                chat_format = "llama-2"
            
            if chat_format:
                response = llm.create_chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2048,
                    temperature=0.7,
                    stop=["</s>", "<end_of_turn>", "<|im_end|>"]  # Různé stop tokeny
                )
                return response['choices'][0]['message']['content']
            else:
                response = llm(prompt, max_tokens=2048, temperature=0.7, echo=False, stop=["</s>", "\n\n\n"])
                return response['choices'][0]['text']
        except Exception as e:
            return f"❌ Chyba GGUF: {str(e)}"

    @staticmethod
    def generuj(prompt, model_id, model_info=None):
        if model_id == 'gemini': return Providers.odpoved_gemini(prompt)
        if model_id == 'deepseek': return Providers.odpoved_deepseek(prompt)
        if model_id == 'openai': return Providers.odpoved_openai(prompt)
        if model_id == 'claude': return Providers.odpoved_claude(prompt)
        
        # Ollama routing
        if model_id.startswith('ollama/'):
            model_name = model_id.replace('ollama/', '')
            return Providers.odpoved_ollama(prompt, model_name)
            
        if isinstance(model_id, str) and model_id.startswith('lokalni_'):
            # Cestu modelu určuje výhradně server; klientské model_info se ignoruje.
            for model in Providers.dostupne_modely():
                if model.get('id') == model_id and model.get('typ') == 'lokalni':
                    cesta = os.path.realpath(model.get('info', {}).get('cesta', ''))
                    koren = os.path.realpath(Config.MODELY_DIR)
                    if os.path.commonpath([koren, cesta]) == koren and os.path.isfile(cesta):
                        return Providers.odpoved_gguf(prompt, cesta)
            return '❌ Lokální model nebyl nalezen nebo není povolen.'
                
        return f"❌ Neznámý model: {model_id}"