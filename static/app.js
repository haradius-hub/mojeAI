let aktualniModel = '';
let dostupneModely = [];
let vybranySoubor = null;

function zobrazToast(zprava, error = false) {
    const toast = document.getElementById('toast');
    toast.textContent = zprava;
    toast.className = 'toast' + (error ? ' error' : '');
    toast.classList.add('show');
    clearTimeout(toast._timeout);
    toast._timeout = setTimeout(() => toast.classList.remove('show'), 4000);
}

// ====== VÝBĚR SLOŽKY PŘES DIALOG ======
async function otevritDialogSlozky() {
    try {
        zobrazToast('⏳ Otevírám okno pro výběr složky...');
        const res = await fetch('/api/vybrat-slozku');
        const data = await res.json();
        if (data.status === 'ok' && data.cesta) {
            document.getElementById('slozkaCesta').value = data.cesta;
            zobrazToast('✅ Složka vybrána');
        }
    } catch (e) {
        zobrazToast('❌ Nepodařilo se otevřít dialog.', true);
    }
}

// ====== ZPRACOVÁNÍ GPU ======
async function nactiGpuInfo() {
    try {
        const res = await fetch('/api/gpu-info');
        const data = await res.json();
        const status = document.getElementById('gpuStatus');
        const detail = document.getElementById('gpuDetail');
        const checkbox = document.getElementById('gpuPovolen');
        
        if (data.dostupna) {
            status.innerHTML = `✅ <span style="color:#238636;">${data.nazev}</span>`;
            
            if (data.cuda) {
                detail.innerHTML = '💡 NVIDIA GPU – akcelerace by měla fungovat.';
                checkbox.disabled = false;
            } else {
                detail.innerHTML = `⚠️ ${data.doporuceni} <a href="https://ollama.com" target="_blank" style="color:#58a6ff;">Stáhnout Ollamu</a>`;
                checkbox.disabled = true;
                checkbox.checked = false;
            }
        } else {
            status.innerHTML = `❌ <span style="color:#da3633;">Žádná GPU</span>`;
            detail.innerHTML = 'Model poběží na CPU.';
            checkbox.disabled = true;
            checkbox.checked = false;
        }
    } catch (e) {
        console.error('Chyba GPU:', e);
        document.getElementById('gpuStatus').textContent = '❌ Nelze detekovat';
    }
}

// ====== NAČTENÍ KONFIGURACE ======
async function nactiKonfiguraci() {
    try {
        const res = await fetch('/api/config');
        const data = await res.json();
        const select = document.getElementById('modelSelect');
        select.innerHTML = '';
        
        let prvniModel = null;
        let prvniModelValue = null;
        
        // Cloudové modely
        const apiModely = ['gemini', 'deepseek', 'openai', 'claude'];
        const dostupneApi = apiModely.filter(m => data.dostupne_modele.some(d => d === m || d.id === m));
        
        if (dostupneApi.length > 0) {
            const group = document.createElement('optgroup');
            group.label = '☁️ Cloudové modely';
            dostupneApi.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m;
                opt.textContent = m.charAt(0).toUpperCase() + m.slice(1);
                group.appendChild(opt);
                if (!prvniModel) { prvniModel = opt.textContent; prvniModelValue = m; }
            });
            select.appendChild(group);
        }
        
        // Lokální modely
        const lokalniModely = data.dostupne_modele.filter(d => typeof d === 'object' && d.typ === 'lokalni');
        if (lokalniModely.length > 0) {
            const group = document.createElement('optgroup');
            group.label = '📁 Lokální modely';
            lokalniModely.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m.id;
                opt.dataset.modelInfo = JSON.stringify(m.info);
                opt.textContent = m.nazev;
                group.appendChild(opt);
                if (!prvniModel) { prvniModel = opt.textContent; prvniModelValue = m.id; }
            });
            select.appendChild(group);
        }

        // Ollama
        const maOllama = data.dostupne_modele.some(d => d.id === 'ollama' || d === 'ollama');
        if (maOllama) {
            const opt = document.createElement('option');
            opt.value = 'ollama';
            opt.textContent = '🦙 Ollama (llama3.2)';
            select.appendChild(opt);
            if (!prvniModel) { prvniModel = opt.textContent; prvniModelValue = 'ollama'; }
        }

        if (!prvniModel) {
            select.innerHTML = '<option value="">❌ Žádný model nenalezen</option>';
            document.getElementById('modelStatus').textContent = '⚠️ Vlož API klíč nebo model do složky modely/';
        } else {
            const vychozi = data.config.vychozi_model || prvniModelValue;
            select.value = vychozi;
            aktualniModel = vychozi;
            const displayName = select.options[select.selectedIndex]?.text || vychozi;
            document.getElementById('modelStatus').textContent = `📍 ${displayName}`;
            document.getElementById('aktivniModel').textContent = `🔹 ${displayName}`;
        }
        
        document.getElementById('systemPrompt').value = data.config.system_prompt || '';
        document.getElementById('internetPovolen').checked = data.config.internet || false;
        document.getElementById('gpuPovolen').checked = data.config.pouzit_gpu || false;
        
        document.getElementById('nCtx').value = data.config.n_ctx || 2048;
        document.getElementById('nThreads').value = data.config.n_threads || 4;
        
        nactiSlozky();
        nactiPamet();
        nactiGpuInfo(); 
        
    } catch (e) {
        console.error('Chyba načítání konfigurace:', e);
        zobrazToast('Chyba načítání konfigurace', true);
    }
}

// ====== ULOŽENÍ API KLÍČE ======
async function ulozKlic() {
    const klic = document.getElementById('apiKlic').value.trim();
    const model = document.getElementById('modelSelect').value;
    
    if (!klic) { zobrazToast('❌ Vlož API klíč!', true); return; }
    
    const apiModely = ['gemini', 'deepseek', 'openai', 'claude'];
    if (!apiModely.includes(model)) { 
        zobrazToast('❌ Pro tento model není potřeba API klíč (nebo vyber cloudový model)', true); 
        return; 
    }
    
    try {
        const res = await fetch('/api/config/keys', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider: model, key: klic })
        });
        const data = await res.json();
        
        if (data.status === 'ok') {
            zobrazToast(`✅ Klíč pro ${model} byl úspěšně uložen.`);
            document.getElementById('apiKlic').value = '';
            setTimeout(nactiKonfiguraci, 1000);
        } else {
            zobrazToast(`❌ Chyba: ${data.zprava}`, true);
        }
    } catch (e) {
        zobrazToast('❌ Chyba komunikace se serverem.', true);
    }
}

// ====== ULOŽENÍ PROMPTU ======
async function ulozPrompt() {
    const prompt = document.getElementById('systemPrompt').value.trim();
    if (!prompt) { zobrazToast('❌ Zadej prompt!', true); return; }
    try {
        await fetch('/api/prompt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: prompt })
        });
        zobrazToast('✅ Prompt uložen');
    } catch (e) {
        zobrazToast('❌ Chyba při ukládání promptu', true);
    }
}

// ====== TOGGLY (INTERNET, GPU) ======
async function ulozInternet() {
    const povolen = document.getElementById('internetPovolen').checked;
    try {
        await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ internet: povolen })
        });
        zobrazToast(povolen ? '✅ Internet povolen' : '❌ Internet zakázán');
    } catch (e) {
        zobrazToast('❌ Chyba', true);
    }
}

async function ulozGpu() {
    const povolen = document.getElementById('gpuPovolen').checked;
    try {
        await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pouzit_gpu: povolen })
        });
        zobrazToast(povolen ? '✅ GPU povolena' : '❌ GPU zakázána');
    } catch (e) {
        zobrazToast('❌ Chyba', true);
    }
}

async function ulozVykon() {
    const n_ctx = parseInt(document.getElementById('nCtx').value);
    const n_threads = parseInt(document.getElementById('nThreads').value);
    if (isNaN(n_ctx) || isNaN(n_threads)) { zobrazToast('❌ Zadej platná čísla', true); return; }
    
    try {
        await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ n_ctx: n_ctx, n_threads: n_threads })
        });
        zobrazToast('✅ Výkon uložen. (Změna se projeví při dalším dotazu)');
    } catch (e) {
        zobrazToast('❌ Chyba při ukládání', true);
    }
}

// ====== SLOŽKY ======
async function pridatSlozku() {
    const cesta = document.getElementById('slozkaCesta').value.trim();
    if (!cesta) { zobrazToast('❌ Zadej cestu ke složce!', true); return; }
    try {
        const res = await fetch('/api/slozka', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cesta: cesta })
        });
        const data = await res.json();
        if (data.status === 'ok') {
            zobrazToast(`✅ ${data.zprava}`);
            document.getElementById('slozkaCesta').value = '';
            nactiSlozky();
            nactiPamet();
        } else {
            zobrazToast(`❌ ${data.zprava}`, true);
        }
    } catch (e) {
        zobrazToast('❌ Chyba při přidávání složky', true);
    }
}

async function nactiSlozky() {
    try {
        const res = await fetch('/api/slozky');
        const data = await res.json();
        const list = document.getElementById('slozkyList');
        if (data.length === 0) {
            list.innerHTML = '<span style="color:#8b949e;">Žádné připojené složky</span>';
        } else {
            list.innerHTML = data.map(s => `
                <div class="slozka-polozka">
                    <span class="cesta">📁 ${s.cesta} ${s.chybi ? '⚠️' : ''}</span>
                    <span class="pocet">${s.pocet || 0} souborů</span>
                    <span class="smazat" onclick="odebratSlozku('${s.cesta.replace(/\\/g, '\\\\')}')">✕</span>
                </div>
            `).join('');
        }
    } catch (e) {
        console.error('Chyba načítání složek:', e);
    }
}

async function odebratSlozku(cesta) {
    try {
        await fetch('/api/slozka', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cesta: cesta })
        });
        nactiSlozky();
        zobrazToast('✅ Složka odebrána');
    } catch (e) {
        zobrazToast('❌ Chyba při odebírání', true);
    }
}

// ====== NAHRÁVÁNÍ SOUBORŮ ======
document.getElementById('fileInput').addEventListener('change', function(e) {
    if (e.target.files.length > 0) {
        vybranySoubor = e.target.files[0];
        zobrazToast(`📎 Připojen: ${vybranySoubor.name}`);
    }
});

// ====== ODESLÁNÍ ZPRÁVY ======
async function poslatDotaz() {
    const input = document.getElementById('userInput');
    let dotaz = input.value.trim();
    
    if (!dotaz && !vybranySoubor) return;
    
    input.value = '';
    input.style.height = 'auto';
    
    // Zjištění explicitního hledání přes //
    let force_search = false;
    if (dotaz.startsWith('//')) {
        force_search = true;
        dotaz = dotaz.substring(2).trim();
    }

    const select = document.getElementById('modelSelect');
    const model = select.value;
    const selectedOption = select.options[select.selectedIndex];
    let modelInfo = null;
    
    if (selectedOption && selectedOption.dataset.modelInfo) {
        try { modelInfo = JSON.parse(selectedOption.dataset.modelInfo); } catch(e) {}
    }
    
    if (!model) { zobrazToast('❌ Není vybraný žádný model', true); return; }
    
    const messages = document.getElementById('messages');
    messages.insertAdjacentHTML('beforeend', `<div class="message user">${escapeHtml(dotaz || '📎 Příloha')}<span class="time">${new Date().toLocaleTimeString()}</span></div>`);
    messages.scrollTop = messages.scrollHeight;
    document.getElementById('statusText').textContent = '⏳ Přemýšlím...';
    
    const formData = new FormData();
    formData.append('dotaz', dotaz);
    formData.append('model', model);
    formData.append('force_search', force_search);
    if (modelInfo) formData.append('lokalni_model_info', JSON.stringify(modelInfo));
    if (vybranySoubor) formData.append('file', vybranySoubor);
    
    vybranySoubor = null;
    document.getElementById('fileInput').value = '';
    
    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        
        // Zpracování odpovědi - barevné odlišení přemýšlení
        let htmlOdpoved = marked.parse(data.odpoved);
        
        // Detekce typických vzorů "přemýšlení"
        // 1. Bloky mezi OTAZKA: a ODPOVED:
        // 2. Věty začínající slovy Nyní, Znovu, Analýza, Rozbor, Tato odpověď, Při tvorbě
        htmlOdpoved = htmlOdpoved.replace(
            /(OTAZKA:[\s\S]*?)(?=ODPOVED:|$)/g,
            '<span class="thinking">$1</span>'
        );
        htmlOdpoved = htmlOdpoved.replace(
            /(Nyní[\s\S]*?)(?=ODPOVED:|$)/g,
            '<span class="thinking">$1</span>'
        );
        
        messages.insertAdjacentHTML('beforeend', `<div class="message assistant">${htmlOdpoved}<span class="time">${new Date().toLocaleTimeString()}</span></div>`);
        messages.scrollTop = messages.scrollHeight;
        document.getElementById('statusText').textContent = '✅ Hotovo';
        nactiPamet();
    } catch (err) {
        messages.insertAdjacentHTML('beforeend', `<div class="message assistant" style="color:#f85149;">❌ Chyba: ${escapeHtml(err.message)}</div>`);
        document.getElementById('statusText').textContent = '❌ Chyba';
        zobrazToast('❌ Chyba komunikace se serverem', true);
    }
}

// ====== PAMĚŤ ======
async function nactiPamet() {
    try {
        const res = await fetch('/api/pamet');
        const data = await res.json();
        const list = document.getElementById('memoryList');
        if (data.length === 0) {
            list.innerHTML = '<div style="color:#8b949e;font-size:12px;">Zatím žádné vzpomínky</div>';
        } else {
            list.innerHTML = data.map(item => `
                <div class="memory-item">
                    <span class="label">📄 ${item.soubor}</span>
                    <span style="color:#8b949e;">${item.obsah.length > 100 ? item.obsah.slice(0,100)+'...' : item.obsah}</span>
                </div>
            `).join('');
        }
    } catch (e) {
        console.error('Chyba načítání paměti:', e);
    }
}

// Pomocná funkce pro escapování
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ====== EVENT LISTENERY ======
document.getElementById('modelSelect').addEventListener('change', function() {
    const selectedOption = this.options[this.selectedIndex];
    const displayName = selectedOption?.text || this.value || 'žádný';
    document.getElementById('aktivniModel').textContent = `🔹 ${displayName}`;
    document.getElementById('modelStatus').textContent = `📍 ${displayName}`;
});

document.getElementById('userInput').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); poslatDotaz(); }
});

document.getElementById('userInput').addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 150) + 'px';
});

// ====== START APLIKACE ======
nactiKonfiguraci();
setInterval(nactiPamet, 15000);