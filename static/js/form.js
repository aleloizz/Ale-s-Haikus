/**
 * @fileoverview Gestione del form di analisi e visualizzazione risultati
 * @author Poetry Analyzer App
 */

import { sanitizeInput, analyzeRhymeStatus, applyStaggeredAnimations } from './utils.js';
import { patterns, requiresRhymeAnalysis } from './patterns.js';
import { publishPoem } from './publish.js';
import { validateCurrentInput, getBlockingStatus, renderIssues, markAnalysisCompleted } from './validation.js'; // (cache bust handled via main.js entrypoint)

/**
 * Gestisce la sottomissione del form di analisi poetica
 * @param {Event} e - Evento di submit
 * @param {Object} elements - Oggetto con gli elementi DOM necessari
 */
export async function handleFormSubmit(e, elements) {
    e.preventDefault();
    
    const { poemText, poemTypeSelect, publishCheckbox } = elements;
    
    // Vibrazione breve come feedback (se supportato)
    if (window.navigator.vibrate) {
        window.navigator.vibrate(7);
    }
    
    const submitBtn = document.getElementById('submitBtn');
    const originalBtnText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    
    // Testo diverso se deve pubblicare
    const shouldPublish = publishCheckbox?.checked;
    const loadingText = shouldPublish ? 
        '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Verificando e pubblicando...' :
        '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Analizzando...';
    
    submitBtn.innerHTML = loadingText;
    
    try {
        // Validazione pre-submit
        const issues = validateCurrentInput({
            text: poemText.value,
            poemType: poemTypeSelect?.value,
            action: 'analyze',
            publishChecked: publishCheckbox?.checked,
            authorValue: document.getElementById('poemAuthor')?.value || ''
        });
        const blocks = getBlockingStatus(issues);
        renderIssues(issues);
        if (blocks.analyze) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
            return;
        }

        const sanitizedText = sanitizeInput(poemText.value);
        const useTolerance = document.getElementById('useTolerance')?.checked || false;
        
        // Prima sempre l'analisi
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                type: poemTypeSelect.value,
                text: sanitizedText,
                use_tolerance: useTolerance
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(
                errorData.message || 
                `Errore ${response.status}: ${response.statusText}`
            );
        }
        
    const data = await response.json();
    showResults(data);
    markAnalysisCompleted(poemText.value);
        
        // Se deve pubblicare e l'analisi è completata (anche se non valida)
        if (shouldPublish && !data.error) {
            const rawAuthor = document.getElementById('poemAuthor')?.value || '';
            const author = rawAuthor.trim() || 'Poeta Anonimo';
            await publishPoem({
                text: sanitizedText,
                poem_type: poemTypeSelect.value,
                title: document.getElementById('poemTitle')?.value.trim() || '',
                author
            }, data.valid);
        }
        
    } catch (error) {
        console.error('Error:', error);
        // Forza issue di tipo error per attivare toast se non già presente
        renderIssues([{ code:'SERVER_ERROR_RUNTIME', severity:'error', message: error.message || 'Errore inatteso durante l\'analisi', blockingActions:{ analyze:true } }]);
        showResults({
            error: true,
            message: error.message
        });
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
    }
}

/**
 * Mostra i risultati dell'analisi poetica
 * @param {Object} data - Dati ricevuti dal server
 */
export function showResults(data) {
    const resultContainer = document.getElementById('resultContainer');
    const resultTitle = document.getElementById('resultTitle');
    const resultMessage = document.getElementById('resultMessage');
    const syllableDetails = document.getElementById('syllableDetails');
    const poemText = document.getElementById('poemText');
    
    if (!resultContainer || !resultTitle || !resultMessage || !syllableDetails) {
        console.error('❌ Elementi risultati non trovati');
        return;
    }
    
    // CLS Prevention: Stabilizza le dimensioni del container prima del display
    if (window.innerWidth >= 992) {
        resultContainer.style.minHeight = '100px';
        resultContainer.style.contain = 'layout style';
    }
    
    resultContainer.style.display = 'block';
    syllableDetails.innerHTML = '';

    // Versi liberi: visualizzazione dedicata
    if (data.poem_type === 'versi_liberi') {
        showVersiLiberiResults(data, resultTitle, resultMessage, syllableDetails, resultContainer);
        return;
    }

    // Gestione errori generici
    if (data.error && !data.error_type) {
        showErrorResults(data, resultTitle, resultMessage, resultContainer);
        return;
    }

    // Gestione errori di struttura (numero versi errato)
    if (data.error && data.error_type) {
        showStructureErrorResults(data, resultTitle, resultMessage, syllableDetails, resultContainer, poemText);
        return;
    }

    // Gestione risultati validi/non validi
    showAnalysisResults(data, resultTitle, resultMessage, syllableDetails, resultContainer);
}

/**
 * Mostra risultati per versi liberi
 */
function showVersiLiberiResults(data, resultTitle, resultMessage, syllableDetails, resultContainer) {
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
    
    // Mostra gruppi con almeno 2 versi che rimano
    Object.entries(rhymeMap).forEach(([rhyme, verses]) => {
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
}

/**
 * Mostra risultati di errore generico
 */
function showErrorResults(data, resultTitle, resultMessage, resultContainer) {
    resultTitle.textContent = "Errore di Analisi";
    resultMessage.innerHTML = `<i class="bi bi-exclamation-triangle-fill"></i> ${data.message || "Si è verificato un errore durante l'analisi"}`;
    resultContainer.querySelector('.alert').className = 'alert alert-danger';
}

/**
 * Mostra risultati di errore di struttura
 */
function showStructureErrorResults(data, resultTitle, resultMessage, syllableDetails, resultContainer, poemText) {
    const lines = poemText.value.split('\n').filter(line => line.trim() !== '');
    const selectedType = poemText.closest('form').querySelector('#poemType').value;
    const requiredLines = patterns[selectedType] ? patterns[selectedType].syllables.length : 0;
    
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
    }
}

/**
 * Mostra risultati dell'analisi metrica
 */
function showAnalysisResults(data, resultTitle, resultMessage, syllableDetails, resultContainer) {
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

    // Costruisci contenuto analisi sillabe
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

    // Analisi rime solo se il tipo di poesia lo richiede
    if (requiresRhymeAnalysis(data.poem_type) && data.rhyme_analysis) {
        contentHTML += renderRhymeAnalysis(data);
    }

    syllableDetails.innerHTML = contentHTML;

    // Applica animazioni dopo l'inserimento del contenuto
    applyStaggeredAnimations('.incorrect-verse, .rhyme-mismatch');
    
    console.log("Dati ricevuti dal backend:", data);
}

/**
 * Renderizza l'analisi delle rime
 * @param {Object} data - Dati dell'analisi
 * @returns {string} HTML dell'analisi rime
 */
function renderRhymeAnalysis(data) {
    if (!data.rhyme_analysis) return "";

    const isValid = data.rhyme_analysis.valid;
    const scheme = data.rhyme_analysis.scheme;
    const errors = data.rhyme_analysis.errors || [];
    const rhymeStatus = analyzeRhymeStatus(data);

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

/**
 * Gestisce l'input nel textarea principale
 * @param {Event} e - Evento input
 * @param {HTMLElement} poemTypeSelect - Select del tipo di poesia
 */
export function handlePoemTextInput(e, poemTypeSelect) {
    // La schermata dei risultati ora rimane visibile fino a quando 
    // l'utente non decide attivamente di fare una nuova analisi.
    // Questo migliora l'esperienza utente evitando che i risultati
    // scompaiano improvvisamente durante la modifica del testo.
    
    // Nota: Il comportamento precedente nascondeva automaticamente 
    // i risultati quando il numero di versi corrispondeva ai requisiti,
    // ma questo creava un'esperienza confusa per l'utente.
}
