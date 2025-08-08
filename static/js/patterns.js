/**
 * @fileoverview Gestione dei pattern poetici e visualizzazione badge
 * @author Poetry Analyzer App
 */

// Definizione dei tipi di poesia disponibili per nazione
export const poemTypes = {
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

// Definizione dei pattern metrici per ogni tipo di poesia
export const patterns = {
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

/**
 * Aggiorna la visualizzazione dei pattern di sillabe
 * @param {string} type - Tipo di poesia
 * @param {HTMLElement} patternDisplay - Elemento DOM dove visualizzare i pattern
 */
export function updatePatternDisplay(type, patternDisplay) {
    console.log('🎯 updatePatternDisplay() chiamata con tipo:', type);
    
    // Controllo di sicurezza
    if (!patternDisplay) {
        console.error('❌ patternDisplay non disponibile');
        return;
    }
    
    if (!type) {
        console.warn('⚠️ Tipo non specificato, uso haiku');
        type = 'haiku';
    }
    
    const pattern = patterns[type];
    if (!pattern) {
        console.warn('⚠️ Pattern non trovato per tipo:', type, '- uso haiku');
        // Fallback sicuro a haiku
        patternDisplay.innerHTML = `
            <span class="badge bg-haiku-secondary syllable-badge">5</span>
            <span class="badge bg-haiku-secondary syllable-badge">7</span>
            <span class="badge bg-haiku-secondary syllable-badge">5</span>
        `;
        return;
    }

    console.log('📋 Pattern trovato:', pattern);

    // Preserve height during content change to prevent CLS
    const currentHeight = patternDisplay.offsetHeight;
    patternDisplay.style.minHeight = currentHeight + 'px';
    
    // Gestione speciale per versi liberi
    if (type === 'versi_liberi') {
        patternDisplay.innerHTML = `
            <span class="badge bg-haiku-secondary syllable-badge">Nessun vincolo metrico</span>
            <div class="mt-2 small text-muted">
                Libera la tua creatività, ogni verso sarà analizzato per sillabe e rime.
            </div>
        `;
        console.log('✅ Pattern "versi liberi" applicato');
        // Reset min-height after content settles
        setTimeout(() => patternDisplay.style.minHeight = '', 50);
        return;
    }

    // Genera badge per le sillabe
    let html = pattern.syllables.map(count => `
        <span class="badge bg-haiku-secondary syllable-badge">${count}</span>
    `).join('');

    // Mostra schema rimico solo se richiesto dal tipo di poesia
    if (pattern.rhyme && pattern.rhyme !== null) {
        html += `<div class="mt-2 rhyme-pattern small text-muted">
            <i class="bi bi-music-note-beamed"></i> Schema: ${pattern.rhyme.join(' ')}
        </div>`;
    }

    patternDisplay.innerHTML = html;
    // Reset min-height after content settles
    setTimeout(() => patternDisplay.style.minHeight = '', 50);
    console.log('✅ Pattern HTML aggiornato per tipo:', type);
}

/**
 * Inizializza la visualizzazione dei badge
 * @param {string} currentType - Tipo di poesia corrente
 * @param {HTMLElement} patternDisplay - Elemento DOM per i pattern
 */
export function initBadges(currentType, patternDisplay) {
    console.log('🔧 initBadges() chiamata');
    
    // Controllo di sicurezza base
    if (!patternDisplay) {
        console.error('❌ patternDisplay non trovato in initBadges');
        return;
    }
    
    // Usa il tipo corrente o haiku come fallback
    const typeToUse = currentType || 'haiku';
    console.log('📊 initBadges - Tipo da usare:', typeToUse);
    
    // Chiama updatePatternDisplay che ha le sue protezioni
    updatePatternDisplay(typeToUse, patternDisplay);
}

/**
 * Popola il select con i tipi di poesia per una nazione
 * @param {string} nation - Nazione selezionata
 * @param {HTMLElement} poemTypeSelect - Elemento select da popolare
 * @param {Function} updateCallback - Callback per aggiornare i pattern
 * @param {boolean} triggerChange - Se scatenare l'evento change
 */
export function populatePoemTypes(nation, poemTypeSelect, updateCallback, triggerChange = true) {
    if (!poemTypeSelect) {
        console.warn('⚠️ poemTypeSelect non disponibile in populatePoemTypes');
        return;
    }
    
    if (!nation || !poemTypes[nation]) {
        console.warn('⚠️ Nazione non valida:', nation);
        return;
    }
    
    // Svuota e riempie il select
    poemTypeSelect.innerHTML = '';
    poemTypes[nation].forEach(pt => {
        const opt = document.createElement('option');
        opt.value = pt.value;
        opt.textContent = pt.label;
        poemTypeSelect.appendChild(opt);
    });

    // Aggiorna sempre i badge dopo aver popolato il select
    if (updateCallback) {
        updateCallback(poemTypeSelect.value);
    }

    // Scatena l'evento change se richiesto
    if (triggerChange) {
        poemTypeSelect.dispatchEvent(new Event('change'));
    }
}

/**
 * Verifica se un tipo di poesia richiede l'analisi delle rime
 * @param {string} type - Tipo di poesia
 * @returns {boolean} True se richiede analisi rime
 */
export function requiresRhymeAnalysis(type) {
    const pattern = patterns[type];
    return pattern && pattern.rhyme !== null;
}
