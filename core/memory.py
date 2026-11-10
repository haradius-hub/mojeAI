# core/memory.py
import os
import sqlite3
import hashlib
import json
import math
from datetime import datetime
from llama_cpp import Llama
from config import Config

class MemoryManager:
    def __init__(self):
        self.db_path = os.path.join(Config.DATA_DIR, "pamet.db")
        self.model_path = os.path.join(Config.MODELY_DIR, "nomic-embed-text-v1.5.Q8_0.gguf")
        
        self.llm = None
        self.db = self._pripoj_db()
        
    def _pripoj_db(self):
        db = sqlite3.connect(self.db_path, check_same_thread=False)
        db.execute("""
            CREATE TABLE IF NOT EXISTS pamet (
                id TEXT PRIMARY KEY,
                text TEXT,
                zdroj TEXT,
                cas TEXT,
                embedding TEXT
            )
        """)
        db.commit()
        return db

    def _ziskej_llm(self):
        if self.llm is None:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Chybi model: {self.model_path}. Spust 'python stahni_model.py'")
            self.llm = Llama(
                model_path=self.model_path,
                embedding=True,
                n_ctx=2048,
                n_threads=4,
                verbose=False
            )
        return self.llm

    def _vytvor_embedding(self, text):
        llm = self._ziskej_llm()
        vysledek = llm.create_embedding(text)
        return vysledek['data'][0]['embedding']

    def _cosine_similarity(self, vec1, vec2):
        # Vypocita kosinovou podobnost dvou vektoru v cistem Pythonu
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)

    def uloz(self, text, zdroj="chat", metadata=None):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_id = hashlib.md5(f"{timestamp}{text[:50]}".encode()).hexdigest()[:12]
        doc_id = f"id_{timestamp}_{hash_id}"
        
        soubor = os.path.join(Config.PAMET_DIR, f"{timestamp}_{hash_id}.txt")
        with open(soubor, "w", encoding="utf-8") as f:
            f.write(text)
        
        try:
            embedding = self._vytvor_embedding(text)
            embedding_json = json.dumps(embedding)
            
            self.db.execute(
                "INSERT INTO pamet (id, text, zdroj, cas, embedding) VALUES (?, ?, ?, ?, ?)",
                (doc_id, text, zdroj, timestamp, embedding_json)
            )
            self.db.commit()
        except Exception as e:
            print(f"Chyba pri ukladani do pameti: {e}")

    def hledej(self, dotaz, pocet=5):
        try:
            query_embedding = self._vytvor_embedding(f"search_query: {dotaz}")
            
            cursor = self.db.execute("SELECT text, embedding FROM pamet WHERE embedding IS NOT NULL")
            vysledky = []
            
            for text, embedding_json in cursor.fetchall():
                embedding = json.loads(embedding_json)
                skore = self._cosine_similarity(query_embedding, embedding)
                vysledky.append((text, skore))
            
            vysledky.sort(key=lambda x: x[1], reverse=True)
            return [text for text, _ in vysledky[:pocet]]
            
        except Exception as e:
            print(f"Chyba pri hledani v pameti: {e}")
            return []

    def ziskej_posledni(self, limit=30):
        import glob
        soubory = sorted(glob.glob(os.path.join(Config.PAMET_DIR, "*.txt")), reverse=True)
        obsah = []
        for soubor in soubory[:limit]:
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
        return obsah

memory_manager = MemoryManager()