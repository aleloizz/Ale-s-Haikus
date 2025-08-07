/**
 * @fileoverview Utilità generiche per l'applicazione di analisi poetica
 * @author Poetry Analyzer App
 */

/**
 * Sanifica l'input dell'utente rimuovendo caratteri pericolosi
 * @param {string} input - Testo da sanificare
 * @returns {string} Testo sanificato
 */
export function sanitizeInput(input) {
    if (typeof input !== 'string') return '';
    return input
        .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
        .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '')
        .replace(/javascript:/gi, '')
        .replace(/on\w+\s*=/gi, '')
        .trim();
}

/**
 * Copia testo negli appunti con fallback per dispositivi non supportati
 * @param {string} text - Testo da copiare
 * @returns {Promise<boolean>} Successo dell'operazione
 */
export async function copyToClipboard(text) {
    try {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(text);
        } else {
            // Fallback per browser non supportati
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.left = '-9999px';
            document.body.appendChild(textarea);
            textarea.focus();
            textarea.select();
            const success = document.execCommand('copy');
            document.body.removeChild(textarea);
            if (!success) throw new Error('Copy command failed');
        }
        return true;
    } catch (err) {
        console.error('Copy failed:', err);
        return false;
    }
}

/**
 * Aggiunge vibrazione se supportata dal dispositivo
 * @param {number} duration - Durata in millisecondi
 */
export function vibrate(duration = 7) {
    if (window.navigator.vibrate) {
        window.navigator.vibrate(duration);
    }
}

/**
 * Estrae le ultime n sillabe da un verso per l'analisi delle rime
 * @param {Object|string} versoObj - Oggetto verso o stringa
 * @param {number} n - Numero di sillabe da estrarre
 * @returns {string} Sillabe estratte
 */
export function estrai_ultime_sillabe(versoObj, n = 2) {
    if (versoObj && typeof versoObj === 'object' && Array.isArray(versoObj.syllables)) {
        const sillabe = versoObj.syllables;
        if (sillabe.length === 0) return '';
        return sillabe.slice(-n).join('');
    }
    if (typeof versoObj === 'string') {
        const parole = versoObj.trim().split(/\s+/);
        if (parole.length === 0) return '';
        const ultimaParola = parole[parole.length - 1].toLowerCase();
        return ultimaParola.slice(-3);
    }
    return '';
}

/**
 * Analizza lo stato delle rime per la visualizzazione
 * @param {Object} data - Dati dall'analisi del server
 * @returns {Array<string>} Array con stato di ogni verso ('valid'|'invalid')
 */
export function analyzeRhymeStatus(data) {
    // Usa lo stato delle rime calcolato dal server Python invece di ricalcolarlo qui
    if (data.rhyme_analysis?.verse_status) {
        return data.rhyme_analysis.verse_status;
    }
    
    // Fallback alla logica originale se verse_status non è disponibile
    if (!data.rhyme_analysis?.scheme || !data.results) return [];

    const status = Array(data.results.length).fill('valid');
    const rhymeMap = {};

    let verseIndex = 0;
    data.rhyme_analysis.scheme.forEach(group => {
        group.split('').forEach(letter => {
            if (!rhymeMap[letter]) rhymeMap[letter] = [];
            rhymeMap[letter].push(verseIndex++);
        });
    });

    Object.entries(rhymeMap).forEach(([letter, verses]) => {
        if (verses.length <= 1) return;

        const referenceRhyme = estrai_ultime_sillabe(data.results[verses[0]].text);
        
        for (let i = 1; i < verses.length; i++) {
            const currentRhyme = estrai_ultime_sillabe(data.results[verses[i]].text);
            if (currentRhyme !== referenceRhyme) {
                verses.forEach(v => status[v] = 'invalid');
                break;
            }
        }
    });

    return status;
}

/**
 * Applica animazioni con ritardo casuale agli elementi
 * @param {string} selector - Selettore CSS degli elementi
 * @param {string} animationClass - Classe di animazione da applicare
 */
export function applyStaggeredAnimations(selector, animationClass = 'animate__headShake') {
    setTimeout(() => {
        document.querySelectorAll(selector).forEach(el => {
            el.classList.add('animate__animated', animationClass);
            el.style.animationDelay = `${Math.random() * 0.3}s`;
        });
    }, 50);
}

/**
 * Mostra un toast Bootstrap
 * @param {string} toastId - ID del toast da mostrare
 */
export function showBootstrapToast(toastId) {
    const toastElement = document.getElementById(toastId);
    if (toastElement && window.bootstrap) {
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
    }
}
