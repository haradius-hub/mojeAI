# routes/chat.py
from flask import Blueprint, request, jsonify, send_file
from config import Config
from core.memory import memory_manager
from core.providers import Providers
from core.conversations import conversation_manager, ConversationError
from core.file_processing import extract_document_text
from datetime import datetime
import requests
import os
import tempfile
from werkzeug.utils import secure_filename
import json
import hashlib
import uuid
from ddgs import DDGS

chat_bp = Blueprint('chat', __name__)

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_HISTORY_MESSAGES = 12
MAX_HISTORY_CHARS = 24000


def _saved_attachment_text(attachment):
    """Read only supported text/document attachments from the managed data directory."""
    relative = attachment.get("storage_path", "")
    root = os.path.realpath(Config.DATA_DIR)
    path = os.path.realpath(os.path.join(root, relative))
    if os.path.commonpath([root, path]) != root or not os.path.isfile(path):
        return ""
    extension = os.path.splitext(attachment.get("original_name", ""))[1].lower()
    try:
        if extension == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(path)
            return "\n".join((page.extract_text() or "") for page in reader.pages[:100])[:12000]
        if extension in {".docx", ".xlsx", ".pptx", ".odt", ".ods", ".odp"}:
            return extract_document_text(path, extension)[:12000]
        if extension in {
            ".txt", ".md", ".py", ".csv", ".htm", ".html", ".css", ".js"
        }:
            with open(path, "r", encoding="utf-8-sig") as file:
                return file.read(12000)
    except Exception as exc:
        print(
            f"[VAROVANI] Starší přílohu {attachment.get('original_name', '')} "
            f"nelze načíst: {type(exc).__name__}: {exc}"
        )
    return ""


def _build_history_context(messages, max_chars=MAX_HISTORY_CHARS):
    """Build a bounded chronological context; the database history remains complete."""
    selected = []
    remaining = max_chars
    for message in reversed(messages[-MAX_HISTORY_MESSAGES:]):
        if message.get("role") not in {"user", "assistant"}:
            continue
        content = (message.get("content") or "").strip()
        attachment_parts = []
        for attachment in message.get("attachments", []):
            extracted = _saved_attachment_text(attachment)
            if extracted:
                attachment_parts.append(
                    f"[Dříve přiložený soubor: {attachment.get('original_name', 'soubor')}]\n{extracted}"
                )
        if attachment_parts:
            content += "\n\n" + "\n\n".join(attachment_parts)
        if len(content) > remaining:
            content = content[-remaining:]
        if not content:
            break
        selected.append((message["role"], content))
        remaining -= len(content)
        if remaining <= 0:
            break
    selected.reverse()
    if not selected:
        return "Žádné předchozí zprávy."
    labels = {"user": "UŽIVATEL", "assistant": "ASISTENT"}
    return "\n\n".join(
        f"{labels[role]}:\n{content}" for role, content in selected
    )


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
        conversation_id = request.form.get('conversation_id') or None
        model_info = None  # Cesta modelu se nikdy nepřebírá od klienta.
        nahrany_soubor = request.files.get('file')
    else:
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            return jsonify({'odpoved': 'Neplatný formát požadavku.'}), 400
        dotaz = data.get('dotaz', '')
        model_id = data.get('model', 'gemini')
        force_search = data.get('force_search', False)
        conversation_id = data.get('conversation_id') or None
        model_info = None  # Cesta modelu se nikdy nepřebírá od klienta.
        nahrany_soubor = None

    if not isinstance(dotaz, str) or len(dotaz) > 20000:
        return jsonify({'odpoved': 'Dotaz musí být text do 20 000 znaků.'}), 400
    if not isinstance(model_id, str) or len(model_id) > 200:
        return jsonify({'odpoved': 'Neplatný identifikátor modelu.'}), 400
    if not isinstance(force_search, bool):
        return jsonify({'odpoved': 'Neplatná hodnota force_search.'}), 400
    if conversation_id is not None and (
        not isinstance(conversation_id, str) or not conversation_id.strip()
        or len(conversation_id) > 128
    ):
        return jsonify({'odpoved': 'Neplatné ID konverzace.'}), 400
    if not dotaz and not nahrany_soubor:
        return jsonify({'odpoved': 'Prosim napis otazku nebo nahraj soubor.'})

    text_ze_souboru = ""
    upload_bytes = None
    upload_original_name = None
    upload_mime_type = None
    upload_extension = None
    if nahrany_soubor:
        puvodni_nazev = secure_filename(nahrany_soubor.filename or '')
        pripona = os.path.splitext(puvodni_nazev)[1].lower()
        povolene_pripony = {
            '.pdf', '.txt', '.md', '.py', '.csv', '.htm', '.html', '.css', '.js',
            '.docx', '.xlsx', '.pptx', '.odt', '.ods', '.odp'
        }
        if pripona not in povolene_pripony:
            return jsonify({'odpoved': 'Nepodporovaný typ souboru.'}), 400
        temp_file = tempfile.NamedTemporaryFile(prefix='mojeai_', suffix=pripona, delete=False)
        cesta = temp_file.name
        temp_file.close()
        try:
            nahrany_soubor.save(cesta)
            upload_size = os.path.getsize(cesta)
            if upload_size > MAX_UPLOAD_BYTES:
                return jsonify({'odpoved': 'Soubor překračuje limit 25 MB.'}), 413
            if pripona == '.pdf':
                from pypdf import PdfReader
                reader = PdfReader(cesta)
                casti = []
                zbyva = 100000
                for page in reader.pages[:300]:
                    cast = page.extract_text() or ''
                    casti.append(cast[:zbyva])
                    zbyva -= len(casti[-1])
                    if zbyva <= 0:
                        break
                text_ze_souboru = "\n".join(casti)
            elif pripona in {'.docx', '.xlsx', '.pptx', '.odt', '.ods', '.odp'}:
                text_ze_souboru = extract_document_text(cesta, pripona)
            else:
                with open(cesta, 'r', encoding='utf-8-sig') as f:
                    text_ze_souboru = f.read(100001)
                if len(text_ze_souboru) > 100000:
                    return jsonify({'odpoved': 'Textový obsah souboru překračuje limit 100 000 znaků.'}), 413
            with open(cesta, 'rb') as uploaded_file:
                upload_bytes = uploaded_file.read()
            upload_original_name = (nahrany_soubor.filename or 'soubor')[:255]
            upload_mime_type = nahrany_soubor.mimetype
            upload_extension = pripona
        except ValueError as e:
            kod = 413 if 'překračuje limit' in str(e) or 'překračuje bezpečnostní limit' in str(e) else 400
            return jsonify({'odpoved': str(e)}), kod
        except Exception as e:
            print(f"[CHYBA] Nepodařilo se přečíst nahraný soubor: {type(e).__name__}: {e}")
            return jsonify({'odpoved': 'Soubor se nepodařilo přečíst. Může být poškozený nebo mít nepodporovaný obsah.'}), 400
        finally:
            if os.path.exists(cesta):
                os.remove(cesta)

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

    previous_messages = []
    parent_message_id = None
    if conversation_id:
        try:
            previous_messages = conversation_manager.get_recent_messages(
                conversation_id, limit=MAX_HISTORY_MESSAGES
            )
            if previous_messages and previous_messages[-1].get("role") == "assistant":
                parent_message_id = previous_messages[-1]["id"]
        except ConversationError as exc:
            return jsonify({'odpoved': str(exc)}), 400

    history_budget = MAX_HISTORY_CHARS
    if model_id.startswith(("ollama/", "lokalni_")):
        try:
            local_context_size = max(512, int(config.get("n_ctx", 2048)))
        except (TypeError, ValueError):
            local_context_size = 2048
        history_budget = min(MAX_HISTORY_CHARS, local_context_size)
        file_budget = min(100000, local_context_size * 2)
        if len(text_ze_souboru) > file_budget:
            text_ze_souboru = (
                text_ze_souboru[:file_budget]
                + "\n[Obsah souboru byl zkrácen podle velikosti kontextu lokálního modelu.]"
            )
    historie_info = _build_history_context(previous_messages, history_budget)
    soubor_info = (
        f"\nOBSAH AKTUÁLNĚ NAHRANÉHO SOUBORU:\n{text_ze_souboru}\n"
        if text_ze_souboru else ""
    )

    prompt = f"""{config.get('system_prompt')}
Aktualni datum a cas: {ted}
PAMET:
{kontext}
{internet_info}
PŘEDCHOZÍ PRŮBĚH KONVERZACE:
{historie_info}
{soubor_info}
OTAZKA: {dotaz}
ODPOVED:"""

    # Uživatelova zpráva se uloží před voláním modelu.
    try:
        if not conversation_id:
            nazev = (dotaz.strip() or upload_original_name or "Nová konverzace")[:200]
            conversation = conversation_manager.create_conversation(title=nazev)
            conversation_id = conversation["id"]

        provider = (
            "ollama" if model_id.startswith("ollama/")
            else "local" if model_id.startswith("lokalni_")
            else model_id
        )
        user_message = conversation_manager.add_message(
            conversation_id, "user", dotaz, parent_message_id=parent_message_id,
            provider=provider, model=model_id
        )

        if upload_bytes is not None:
            upload_dir = os.path.join(Config.DATA_DIR, "uploads", conversation_id)
            os.makedirs(upload_dir, exist_ok=True)
            safe_name = secure_filename(upload_original_name or "") or ("soubor" + (upload_extension or ""))
            stored_name = uuid.uuid4().hex + "_" + safe_name
            absolute_path = os.path.join(upload_dir, stored_name)
            relative_path = os.path.relpath(
                absolute_path, Config.DATA_DIR
            ).replace("\\", "/")
            try:
                with open(absolute_path, "wb") as stored_file:
                    stored_file.write(upload_bytes)
                conversation_manager.add_attachment(
                    user_message["id"], upload_original_name, relative_path,
                    upload_mime_type, len(upload_bytes),
                    hashlib.sha256(upload_bytes).hexdigest(),
                )
            except Exception:
                if os.path.exists(absolute_path):
                    os.remove(absolute_path)
                raise
    except ConversationError as e:
        return jsonify({'odpoved': str(e)}), 400
    except Exception as e:
        print(f"[CHYBA] Uložení uživatelské zprávy do historie selhalo: {type(e).__name__}: {e}")
        return jsonify({'odpoved': 'Zprávu se nepodařilo bezpečně uložit do historie. Model nebyl spuštěn.'}), 500

    memory_manager.uloz(f"Otazka: {dotaz}", zdroj="dotaz")
    zacatek_generovani = datetime.now()
    try:
        odpoved = Providers.generuj(prompt, model_id)
        if not isinstance(odpoved, str):
            odpoved = str(odpoved)
        failed = odpoved.lstrip().startswith("❌")
        error_code = "provider_error" if failed else None
        status = "failed" if failed else "completed"
    except Exception as e:
        print(f"[CHYBA] Generování odpovědi selhalo: {type(e).__name__}: {e}")
        odpoved = f"❌ Chyba při generování odpovědi ({type(e).__name__}). Uživatelský dotaz byl uložen."
        status = "failed"
        error_code = type(e).__name__[:200]

    duration_ms = max(0, int((datetime.now() - zacatek_generovani).total_seconds() * 1000))
    try:
        assistant_message = conversation_manager.add_message(
            conversation_id, "assistant", odpoved,
            parent_message_id=user_message["id"], provider=provider,
            model=model_id, status=status, error_code=error_code,
            duration_ms=duration_ms
        )
    except Exception as e:
        print(f"[CHYBA] Uložení odpovědi do historie selhalo: {type(e).__name__}: {e}")
        return jsonify({
            'odpoved': odpoved,
            'conversation_id': conversation_id,
            'user_message_id': user_message["id"],
            'historie_chyba': 'Odpověď se nepodařilo uložit do historie.'
        }), 500

    memory_manager.uloz(f"Odpoved: {odpoved}", zdroj="odpoved")

    return jsonify({
        'odpoved': odpoved,
        'conversation_id': conversation_id,
        'user_message_id': user_message["id"],
        'assistant_message_id': assistant_message["id"],
        'status': status
    })

@chat_bp.route("/api/conversations", methods=["GET"])
def list_conversations():
    try:
        limit = int(request.args.get("limit", 100))
        offset = int(request.args.get("offset", 0))
        search = request.args.get("q", "").strip()
        items = conversation_manager.list_conversations(
            limit=limit, offset=offset, search=search
        )
        return jsonify({"conversations": items, "limit": limit, "offset": offset})
    except (ValueError, ConversationError) as exc:
        return jsonify({"error": str(exc)}), 400


@chat_bp.route("/api/conversations/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    try:
        conversation = conversation_manager.get_conversation(conversation_id)
        for message in conversation.get("messages", []):
            for attachment in message.get("attachments", []):
                attachment.pop("storage_path", None)
                attachment.pop("sha256", None)
        return jsonify(conversation)
    except ConversationError as exc:
        return jsonify({"error": str(exc)}), 404


@chat_bp.route("/api/conversations/<conversation_id>/pin", methods=["POST"])
def set_conversation_pin(conversation_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("pinned"), bool):
        return jsonify({"error": "Očekávána boolean hodnota pinned."}), 400
    try:
        return jsonify(conversation_manager.set_pinned(
            conversation_id, data["pinned"]
        ))
    except ConversationError as exc:
        return jsonify({"error": str(exc)}), 400


@chat_bp.route("/api/conversations/pinned-order", methods=["POST"])
def reorder_pinned_conversations():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Očekávána JSON data."}), 400
    try:
        order = conversation_manager.reorder_pinned(data.get("conversation_ids"))
        return jsonify({"status": "ok", "conversation_ids": order})
    except ConversationError as exc:
        return jsonify({"error": str(exc)}), 400


@chat_bp.route("/api/attachments/<attachment_id>", methods=["GET"])
def download_attachment(attachment_id):
    try:
        attachment = conversation_manager.get_attachment(attachment_id)
        root = os.path.realpath(Config.DATA_DIR)
        path = os.path.realpath(os.path.join(root, attachment["storage_path"]))
        if os.path.commonpath([root, path]) != root or not os.path.isfile(path):
            return jsonify({"error": "Soubor přílohy nebyl nalezen."}), 404
        return send_file(
            path, as_attachment=True,
            download_name=attachment["original_name"],
            mimetype=attachment.get("mime_type") or "application/octet-stream",
        )
    except ConversationError as exc:
        return jsonify({"error": str(exc)}), 404
