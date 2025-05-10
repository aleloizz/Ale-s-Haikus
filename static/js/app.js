const poemTypes = { // Tipi di poesia disponibili
    italiane: [
        { value: "sonetto", label: "Sonetto" },
        { value: "quartina", label: "Quartina" },
        { value: "stornello", label: "Stornello" },
        { value: "ottava_rima", label: "Ottava rima" },
        { value: "terzina_dantesca", label: "Terzina dantesca" },
        { value: "versi_liberi", label: "Versi liberi" }
    ],
    giapponesi: [
        { value: "haiku", label: "Haiku" },
        { value: "tanka", label: "Tanka" },
        { value: "katauta", label: "Katauta" },
        { value: "choka", label: "Choka" },
        { value: "sedoka", label: "Sedoka" }
    ],
    inglesi: [
        { value: "limerick", label: "Limerick" },
        { value: "ballad", label: "Ballad" },
        { value: "clerihew", label: "Clerihew" },
        { value: "cinquain", label: "Cinquain" }
    ]
};

document.addEventListener('DOMContentLoaded', () => {
    // Elementi UI
    const poemNation = document.getElementById('poemNation');
    const poemTypeSelect = document.getElementById('poemType');
    const patternDisplay = document.getElementById('patternDisplay');
    const poemText = document.getElementById('poemText');
    const poemForm = document.getElementById('poemForm');
    const copyBtn = document.getElementById('copyBtn');

    // Limite di caratteri lato frontend
    poemText.setAttribute('maxlength', 500);

    // Funzione di sanitizzazione base (rimuove tag HTML)
    function sanitizeInput(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // Popolamento del selettore dei tipi di poesia in base alla nazione
    function populatePoemTypes(nation) {
        poemTypeSelect.innerHTML = '';
        poemTypes[nation].forEach(pt => {
            const opt = document.createElement('option');
            opt.value = pt.value;
            opt.textContent = pt.label;
            poemTypeSelect.appendChild(opt);
        });
        poemTypeSelect.dispatchEvent(new Event('change'));
    }

    poemNation.addEventListener('change', () => {
        populatePoemTypes(poemNation.value);
    });

    // Popola all'avvio
    populatePoemTypes(poemNation.value);
   
    // Configurazione iniziale
    document.body.classList.remove('loading');

    // Pattern disponibili
    const patterns = {
        'haiku': { syllables: [5, 7, 5], rhyme: null },
        'tanka': { syllables: [5, 7, 5, 7, 7], rhyme: null },
        'katauta': { syllables: [5, 7, 7], rhyme: null },
        'choka': { syllables: [5, 7, 5, 7, 5, 7, 5, 7, 7], rhyme: null },
        'sedoka': { syllables: [5, 7, 7, 5, 7, 7], rhyme: null },
        'sonetto': { syllables: Array(14).fill(11), rhyme: ["ABBA", "ABBA", "CDC", "DCD"] },
        'stornello': { syllables: [5, 11, 11], rhyme: ["ABA"] },
        'quartina': { syllables: Array(4).fill(11), rhyme: ["ABAB"] },
        'ottava_rima': { syllables: Array(8).fill(11), rhyme: ["ABABABCC"] },
        'terzina_dantesca': { syllables: [11, 11, 11], rhyme: ["ABA"] },
        'versi_liberi': { syllables: [], rhyme: null },
        'limerick': { syllables: [8, 8, 5, 5, 8], rhyme: ["AABBA"] },
        'ballad': { syllables: [8, 6, 8, 6], rhyme: ["ABCB"] },  
        'clerihew': { syllables: [8, 8, 8, 8], rhyme: ["AABB"] }, 
        'cinquain': { syllables: [2, 4, 6, 8, 2], rhyme: null }
    };

    function updatePatternDisplay(type) {
        const pattern = patterns[type];
        if (!pattern) return;

        if (type === 'versi_liberi') {
            patternDisplay.innerHTML = `
                <span class="badge bg-haiku-secondary syllable-badge">Nessun vincolo metrico</span>
                <div class="mt-2 small text-muted">
                    Libera la tua creatività, ogni verso sarà analizzato per sillabe e rime.
                </div>
            `;
            return;
        }

        let html = pattern.syllables.map(count => `
            <span class="badge bg-haiku-secondary syllable-badge">${count}</span>
        `).join('');

        if (pattern.rhyme) {
            html += `<div class="mt-2 rhyme-pattern small text-muted">
                    <i class="bi bi-music-note-beamed"></i> ${pattern.rhyme.join(' ')}
                </div>`;
        }

        patternDisplay.innerHTML = html;
    }

    // Inizializza i badge
    function initBadges() {
        updatePatternDisplay('haiku');
    }

    // Micro-interazioni
    poemText.addEventListener('focus', () => {
        poemText.style.borderColor = 'var(--primary)';
        const firstBadge = patternDisplay.querySelector('.badge');
        if (firstBadge) firstBadge.classList.add('pulse');
    });

    poemText.addEventListener('blur', () => {
        poemText.style.borderColor = '';
    });

    // Cambio tipo poesia
    poemTypeSelect.addEventListener('change', () => {
        const selectedType = poemTypeSelect.value;
        updatePatternDisplay(selectedType);

        if (selectedType === 'versi_liberi') {
            poemText.placeholder = "Non ti ferma più nessuno!!";
        } else {
            poemText.placeholder = "Scrivi qui i tuoi versi :3";
        }

        poemTypeSelect.classList.add('animate__pulse');
        setTimeout(() => {
            poemTypeSelect.classList.remove('animate__pulse');
        }, 500);
    });

    // Invio al backend
    poemForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        // Vibrazione breve come feedback (se supportato)
        if (window.navigator.vibrate) {
            window.navigator.vibrate(7);
        }
        const submitBtn = document.getElementById('submitBtn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Analizzando...';
        
        try {
            const sanitizedText = sanitizeInput(poemText.value);
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    type: poemTypeSelect.value,
                    text: sanitizedText
                })
            });
            
            // Sostituire nella fetch:
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(
                    errorData.message || 
                    `Errore ${response.status}: ${response.statusText}`
                );
            }
            
            const data = await response.json();
            showResults(data);
        } catch (error) {
            console.error('Error:', error);
            showResults({
                error: true,
                message: error.message
            });
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-check-circle"></i> Verifica';
        }
    });

    // Animazione selettore tipo poesia
    poemTypeSelect.addEventListener('mouseenter', () => {
        poemTypeSelect.style.transform = 'translateY(-2px)';
    });

    poemTypeSelect.addEventListener('mouseleave', () => {
        poemTypeSelect.style.transform = 'translateY(0)';
    });

    document.querySelectorAll('.rhyme-mismatch').forEach(el => {
        el.classList.add('animate__animated', 'animate__headShake');
        el.style.animationDelay = `${Math.random() * 0.3}s`;
    });

    // Mostra risultati
    function showResults(data) {
        const resultContainer = document.getElementById('resultContainer');
        const resultTitle = document.getElementById('resultTitle');
        const resultMessage = document.getElementById('resultMessage');
        const syllableDetails = document.getElementById('syllableDetails');
        const poemText = document.getElementById('poemText');
        
        resultContainer.style.display = 'block';
        syllableDetails.innerHTML = '';
    
        // Versi liberi: visualizzazione dedicata
        if (data.poem_type === 'versi_liberi') {
            resultTitle.innerHTML = `<i class="bi bi-stars text-accent"></i> Versi liberi`;
            resultMessage.innerHTML = `<span class="text-muted">Analisi delle sillabe e delle rime per ogni verso:</span>`;
            resultContainer.querySelector('.alert').className = 'alert alert-info';

            // Raggruppa versi per rima
            const rhymeMap = {};
            data.results.forEach(res => {
                if (!res.rhyme) return;
                if (!rhymeMap[res.rhyme]) rhymeMap[res.rhyme] = [];
                rhymeMap[res.rhyme].push(res);
            });

            let contentHTML = '';
            Object.entries(rhymeMap).forEach(([rhyme, verses]) => {
                // Mostra solo gruppi con almeno 2 versi che rimano
                if (verses.length > 1 && rhyme) {
                    contentHTML += `<div class="mb-2 verse-detail" style="background:rgba(160,132,232,0.07);border-left:3px solid #a084e8;">
                        <div class="small text-muted mb-1"><i class="bi bi-music-note-beamed"></i> Rima: <strong>${rhyme}</strong></div>
                        ${verses.map(res => `
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>Verso ${res.verse}:</strong> "${res.text}"
                                </div>
                                <span class="badge bg-haiku-secondary">${res.syllables} sillabe</span>
                            </div>
                        `).join('')}
                    </div>`;
                }
            });

            // Mostra anche i versi senza rime (singoli)
            data.results.forEach(res => {
                if (!res.rhyme) return;
                if (rhymeMap[res.rhyme].length === 1) {
                    contentHTML += `<div class="mb-2 verse-detail">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <strong>Verso ${res.verse}:</strong> "${res.text}"
                            </div>
                            <span class="badge bg-haiku-secondary">${res.syllables} sillabe</span>
                        </div>
                    </div>`;
                }
            });

            syllableDetails.innerHTML = contentHTML;
            return;
        }
    
        // Controlla il numero di versi
        const lines = poemText.value.split('\n').filter(line => line.trim() !== '');
        const selectedType = poemTypeSelect.value;
        const requiredLines = patterns[selectedType].length;
    
        // Gestione errori generici
        if (data.error && !data.error_type) {
            resultTitle.textContent = "Errore di Analisi";
            resultMessage.innerHTML = `<i class="bi bi-exclamation-triangle-fill"></i> ${data.message || "Si è verificato un errore durante l'analisi"}`;
            resultContainer.querySelector('.alert').className = 'alert alert-danger';
            return;
        }
    
        // Gestione errori di struttura
        if (data.error && data.error_type) {
            if (lines.length !== requiredLines) {
                let icon, alertClass, title;
                
                if (data.error_type === 'too_few_verses') {
                    icon = '<i class="bi bi-arrow-down-circle-fill"></i>';
                    alertClass = 'alert-warning';
                    title = 'Versi Mancanti';
                } else {
                    icon = '<i class="bi bi-arrow-up-circle-fill"></i>';
                    alertClass = 'alert-danger';
                    title = 'Troppi Versi';
                }
    
                resultTitle.textContent = title;
                resultMessage.innerHTML = `${icon} ${data.message}`;
                resultContainer.querySelector('.alert').className = `alert ${alertClass}`;
    
                const diff = Math.abs(data.required - data.received);
                const verseWord = diff === 1 ? 'verso' : 'versi';
                const typeNames = {
                    'haiku': 'Haiku',
                    'tanka': 'Tanka',
                    'sonetto': 'Sonetto',
                    'quartina': 'Quartina',
                    'limerick': 'Limerick'
                };
                const poemTypeName = typeNames[data.poem_type] || data.poem_type;
                
                syllableDetails.innerHTML = `
                    <div class="verse-count-error ${alertClass.replace('alert-', 'text-')}">
                        <i class="bi ${data.error_type === 'too_few_verses' ? 'bi-info-circle-fill' : 'bi-x-circle-fill'}"></i>
                        ${data.error_type === 'too_few_verses' ? 'Mancano' : 'Rimuovi'} ${diff} ${verseWord}!
                    </div>
                    <div class="pattern-info mt-2">
                        <span class="poem-type-badge">${poemTypeName}</span>
                        <span class="patternDisplay">${data.pattern.join('-')}</span>
                    </div>
                `;
                return;
            }
        }
    
        // Gestione risultati validi/non validi
        const typeNames = {
            'haiku': 'Haiku',
            'tanka': 'Tanka',
            'sonetto': 'Sonetto',
            'quartina': 'Quartina',
            'limerick': 'Limerick'
        };
        const poemTypeName = typeNames[data.poem_type] || data.poem_type;
        const patternStr = data.pattern ? data.pattern.join('-') : '';
    
        if (data.valid) {
            resultTitle.innerHTML = `<i class="bi bi-check-circle-fill text-success"></i> ${poemTypeName} perfetto!`;
            resultMessage.innerHTML = `
                <i class="bi bi-check-circle-fill"></i> Struttura corretta!
                <div class="small mt-1">${patternStr}</div>
            `;
            resultContainer.querySelector('.alert').className = 'alert alert-success';
        } else {
            resultTitle.innerHTML = `<i class="bi bi-exclamation-triangle-fill"></i> ${poemTypeName} da correggere`;
            resultMessage.innerHTML = `
                <i class="bi bi-exclamation-triangle-fill"></i> Problemi nella metrica
                <div class="small mt-1">${patternStr}</div>
            `;
            resultContainer.querySelector('.alert').className = 'alert alert-danger';
        }
    
        // Costruisci tutto il contenuto in una variabile prima di inserirlo
        let contentHTML = data.results.map(res => `
            <div class="mb-2 verse-detail ${res.correct ? '' : 'incorrect-verse'}">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>Verso ${res.verse}:</strong> "${res.text}"
                        ${res.error ? `<div class="text-danger small mt-1"><i class="bi bi-bug-fill"></i> ${res.error}</div>` : ''}
                    </div>
                    <span class="badge ${res.correct ? 'bg-success' : 'bg-danger'}">
                        ${res.syllables}/${res.target}
                        ${res.correct ? '<i class="bi bi-check-lg ms-1"></i>' : '<i class="bi bi-x-lg ms-1"></i>'}
                    </span>
                </div>
                ${!res.correct ? `
                <div class="progress mt-1" style="height: 4px;">
                    <div class="progress-bar ${res.syllables > res.target ? 'bg-danger' : 'bg-warning'}" 
                         style="width: ${Math.min(100, (res.syllables/res.target)*100)}%">
                    </div>
                </div>
                ` : ''}
            </div>
        `).join('');

        // prova controllo rime
        // Sostituisci entrambe le chiamate con:
        if (data.rhyme_analysis) {
            contentHTML += renderRhymeAnalysis(data);
        }
    
        // Inserisci tutto il contenuto in una sola operazione
        syllableDetails.innerHTML = contentHTML;
    
        // Applica animazioni dopo che il contenuto è stato inserito
        setTimeout(() => {
            document.querySelectorAll('.incorrect-verse, .rhyme-mismatch').forEach(el => {
                el.classList.add('animate__animated', 'animate__headShake');
                el.style.animationDelay = `${Math.random() * 0.3}s`;
            });
        }, 50);
        
        // invia dati al backend per il debug
        console.log("Dati ricevuti dal backend:", data);
    }

    // Nuove funzioni di supporto
    function renderRhymeAnalysis(data) {
        if (!data.rhyme_analysis) return "";

        const isValid = data.rhyme_analysis.valid;
        const scheme = data.rhyme_analysis.scheme;
        const errors = data.rhyme_analysis.errors || [];
        const rhymeStatus = analyzeRhymeStatus(data);

        // Numerazione globale dei versi
        let verseCounter = 1;
        let schemeHtml = '';
        if (scheme) {
            schemeHtml = scheme.map((group, groupIdx) => {
                const groupHtml = group.split('').map((letter, letterIdx) => {
                    const status = rhymeStatus[verseCounter - 1];
                    const html = `
                        <div class="rhyme-letter ${status}">
                            <span class="letter">${letter}</span>
                            <span class="verse-indicator">${verseCounter}</span>
                        </div>
                    `;
                    verseCounter++;
                    return html;
                }).join('');
                return `<div class="rhyme-group" data-group="${groupIdx}">${groupHtml}</div>`;
            }).join('');
        }

        return `
            <div class="glass-card p-4 mb-4 rounded-4 border-0 overflow-hidden">
                <div class="d-flex align-items-center gap-3 mb-3">
                    <i class="bi bi-music-note-beamed fs-3" style="color: var(--text)"></i>
                    <h5 class="mb-0">Analisi Struttura Rimica</h5>
                    <span class="badge ${isValid ? 'bg-success' : 'bg-warning'} ms-auto">
                        ${isValid ? 'Valido' : 'Da correggere'}
                    </span>
                </div>
                ${scheme ? `
                    <div class="mb-3">
                        <small class="text-muted d-block mb-1">Schema atteso:</small>
                        <div class="d-flex flex-wrap gap-2 mb-3">
                            ${scheme.map(group => `
                                <span class="badge bg-haiku-secondary">${group}</span>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                <div class="rhyme-scheme-container">
                    ${schemeHtml}
                </div>
                ${errors.length > 0 ? `
                    <div class="alert-glass d-flex gap-2 p-3 mt-3">
                        <i class="bi bi-exclamation-triangle fs-5"></i>
                        <div>
                            ${errors.map(err => `<p class="mb-1 small">${err}</p>`).join('')}
                        </div>
                    </div>
                ` : isValid ? `
                    <div class="success-glass d-flex align-items-center gap-2 p-3 mt-3">
                        <i class="bi bi-check2-circle fs-5"></i>
                        <span>Struttura rimica corretta</span>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    // Nuova funzione per analizzare lo stato di ogni rima
    function analyzeRhymeStatus(data) {
        if (!data.rhyme_analysis?.scheme || !data.results) return [];
    
        const status = Array(data.results.length).fill('valid'); // Default: tutti validi
        const rhymeMap = {}; // Mappa lettera rima -> indici versi
    
        // 1. Costruisci la mappa delle posizioni delle rime
        let verseIndex = 0;
        data.rhyme_analysis.scheme.forEach(group => {
            group.split('').forEach(letter => {
                if (!rhymeMap[letter]) rhymeMap[letter] = [];
                rhymeMap[letter].push(verseIndex++);
            });
        });
    
        // 2. Analizza ogni gruppo di rime
        Object.entries(rhymeMap).forEach(([letter, verses]) => {
            if (verses.length <= 1) return; // Rime singole sono sempre valide
    
            // Prendi la rima di riferimento (primo verso del gruppo)
            const referenceRhyme = estrai_ultime_sillabe(data.results[verses[0]].text);
            
            // Verifica tutti gli altri versi del gruppo
            for (let i = 1; i < verses.length; i++) {
                const currentRhyme = estrai_ultime_sillabe(data.results[verses[i]].text);
                if (currentRhyme !== referenceRhyme) {
                    // Marca TUTTO il gruppo come invalido se c'è almeno un mismatch
                    verses.forEach(v => status[v] = 'invalid');
                    break;
                }
            }
        });
    
        return status;
    }

    /**
     * Estrae le ultime N sillabe da un verso, usando i dati già segmentati dal backend.
     * @param {object|string} versoObj - Oggetto verso (preferito) o stringa (fallback legacy).
     * @param {number} n - Numero di sillabe finali da estrarre (default: 2).
     * @returns {string} - Stringa delle ultime N sillabe unite.
     */
    function estrai_ultime_sillabe(versoObj, n = 2) {
        // Se è un oggetto con la proprietà 'syllables' (come restituito dal backend)
        if (versoObj && typeof versoObj === 'object' && Array.isArray(versoObj.syllables)) {
            const sillabe = versoObj.syllables;
            if (sillabe.length === 0) return '';
            return sillabe.slice(-n).join('');
        }
        // Fallback: se è una stringa (compatibilità con vecchio codice)
        if (typeof versoObj === 'string') {
            const parole = versoObj.trim().split(/\s+/);
            if (parole.length === 0) return '';
            const ultimaParola = parole[parole.length - 1].toLowerCase();
            return ultimaParola.slice(-3);
        }
        return '';
    }

    // Copia testo
    copyBtn.addEventListener('click', async () => {
        try {
            // Prova Clipboard API moderna
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(poemText.value);
            } else {
                // Fallback per browser mobile/vecchi
                const textarea = document.createElement('textarea');
                textarea.value = poemText.value;
                textarea.style.position = 'fixed';
                textarea.style.left = '-9999px';
                document.body.appendChild(textarea);
                textarea.focus();
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
            }
            // Vibrazione breve come feedback (se supportato)
            if (window.navigator.vibrate) {
                window.navigator.vibrate(7);
            }
            const toast = new bootstrap.Toast(document.getElementById('copyToast'));
            toast.show();
        } catch (err) {
            alert('Copia non supportata su questo dispositivo. Seleziona e copia manualmente.');
            console.error('Copy failed:', err);
        }
    });

    // Inizializzazione
    initBadges();

    poemText.addEventListener('input', function() {
        const lines = this.value.split('\n').filter(line => line.trim() !== '');
        const requiredLines = patterns[poemTypeSelect.value].length;
        
        if (lines.length === requiredLines) {
            const errorContainer = document.getElementById('resultContainer');
            if (errorContainer.querySelector('.alert-warning, .alert-danger')) {
                errorContainer.style.display = 'none';
            }
        }
    });
});