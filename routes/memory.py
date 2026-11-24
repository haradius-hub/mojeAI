# routes/memory.py
import os
import glob
import platform
import shutil
import subprocess
from flask import Blueprint, request, jsonify
from config import Config
from core.memory import memory_manager

memory_bp = Blueprint('memory', __name__)


def _vyber_slozku_systemove():
    """Otevře nativní dialog na počítači, na kterém běží MojeAI."""
    system = platform.system()

    if system == 'Windows':
        powershell = shutil.which('powershell') or shutil.which('pwsh')
        if not powershell:
            raise RuntimeError('PowerShell nebyl nalezen.')
        script = r"""
Add-Type -AssemblyName System.Windows.Forms
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = 'Vyber složku, kterou chceš připojit k MojeAI'
$dialog.ShowNewFolderButton = $false
if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
    [Console]::WriteLine($dialog.SelectedPath)
}
"""
        result = subprocess.run(
            [powershell, '-NoProfile', '-STA', '-Command', script],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=300,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or 'Dialog Windows se nepodařilo spustit.'
            raise RuntimeError(detail)
        return result.stdout.strip()

    if system == 'Darwin':
        result = subprocess.run(
            ['osascript', '-e', 'POSIX path of (choose folder with prompt "Vyber složku pro MojeAI")'],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            # Uživatel mohl dialog pouze zrušit.
            if 'User canceled' in result.stderr:
                return ''
            raise RuntimeError(result.stderr.strip() or 'Dialog macOS se nepodařilo spustit.')
        return result.stdout.strip().rstrip('/')

    # Linux: preferujeme systémový dialog; tkinter je záložní možnost.
    for command, args in (
        ('zenity', ['--file-selection', '--directory', '--title=Vyber složku pro MojeAI']),
        ('kdialog', ['--getexistingdirectory', os.path.expanduser('~')])
    ):
        executable = shutil.which(command)
        if executable:
            result = subprocess.run(
                [executable, *args], capture_output=True, text=True, timeout=300
            )
            if result.returncode == 1:
                return ''
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or 'Systémový dialog se nepodařilo otevřít.')
            return result.stdout.strip()

    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        selected = filedialog.askdirectory(
            parent=root, title='Vyber složku pro MojeAI', mustexist=True
        )
        root.destroy()
        return selected
    except Exception as exc:
        raise RuntimeError(
            'Není dostupný dialog složek. Nainstaluj zenity/kdialog nebo podporu tkinter.'
        ) from exc


@memory_bp.route('/api/pamet', methods=['GET'])
def zobraz_pamet():
    return jsonify(memory_manager.ziskej_posledni(30))


@memory_bp.route('/api/vybrat-slozku', methods=['GET'])
def vybrat_slozku():
    try:
        cesta = _vyber_slozku_systemove()
    except subprocess.TimeoutExpired:
        return jsonify({'status': 'error', 'zprava': 'Výběr složky trval příliš dlouho.'}), 504
    except Exception as exc:
        print(f'[CHYBA] Dialog výběru složky: {exc}')
        return jsonify({'status': 'error', 'zprava': str(exc)}), 500

    if not cesta:
        return jsonify({'status': 'cancel'})

    cesta = os.path.realpath(os.path.abspath(cesta))
    if not os.path.isdir(cesta):
        return jsonify({'status': 'error', 'zprava': 'Vybraná složka už neexistuje nebo není dostupná.'}), 400

    return jsonify({'status': 'ok', 'cesta': cesta})


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
