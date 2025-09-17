/**
 * @fileoverview Entry point principale per l'applicazione di analisi poetica
 * @author Poetry Analyzer App
 */

import { copyToClipboard, vibrate, showBootstrapToast } from './utils.js';
import { saveSelectionState, restoreSelectionState } from './storage.js';
import { poemTypes, updatePatternDisplay, initBadges, populatePoemTypes } from './patterns.js';
import { validateCurrentInput, renderIssues, markAnalysisCompleted, attachValidationHandlers } from './validation.js?v=1.3.7';
/**
 * @fileoverview Entry point principale per l'applicazione di analisi poetica
 * Version tracking & cache busting:
 *   Increment APP_VERSION when making changes requiring clients to refetch.
 */

// Increment this to force a new network fetch (mirrors ?v= query in index.html)
export const APP_VERSION = '1.3.7';
import { handlePublishToggle } from './publish.js';
import { handleFormSubmit, showResults, handlePoemTextInput } from './form.js';
    console.log(`🚀 Inizializzazione app.js modulare v${APP_VERSION}`);

console.log(`📚 Poetry Analyzer App - Versione modulare caricata (v${APP_VERSION})`);
let isRestoringState = false;

/**
 * Inizializzazione dell'applicazione (idempotente)
 */
function bootstrap() {
    console.log('🚀 Inizializzazione app.js modulare');

    // Ottenimento elementi DOM
    const elements = getDOMElements();

    if (!elements.poemNation || !elements.poemTypeSelect || !elements.patternDisplay) {
        console.error('❌ Elementi essenziali non trovati');
        return;
    }

    // Configurazione iniziale
    document.body.classList.remove('loading');

    // Setup event listeners
    setupEventListeners(elements);

    // Inizializzazione con delay per assicurarsi che tutto sia caricato
    setTimeout(() => {
        initializeApplication(elements);
        // Segnala al bootstrapper inline che l'app è pronta
        document.dispatchEvent(new CustomEvent('app:ready'));
    }, 100);
}

// Esegui immediatamente se il DOM è già pronto (import dinamico post-DOMContentLoaded)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap, { once: true });
} else {
    bootstrap();
}

/**
 * Ottiene tutti gli elementi DOM necessari
 * @returns {Object} Oggetto con gli elementi DOM
 */
function getDOMElements() {
    return {
        poemNation: document.getElementById('poemNation'),
        poemTypeSelect: document.getElementById('poemType'),
        patternDisplay: document.getElementById('patternDisplay'),
        poemText: document.getElementById('poemText'),
        poemForm: document.getElementById('poemForm'),
        copyBtn: document.getElementById('copyBtn'),
        publishCheckbox: document.getElementById('publishPoem'),
        publishFields: document.getElementById('publishFields'),
        submitBtnText: document.getElementById('submitBtnText')
    };
}

/**
 * Configura tutti gli event listeners
 * @param {Object} elements - Elementi DOM
 */
function setupEventListeners(elements) {
    const { poemNation, poemTypeSelect, poemText, poemForm, copyBtn, publishCheckbox, patternDisplay } = elements;
    
    // Event listener per cambio nazione
    if (poemNation) {
        poemNation.addEventListener('change', () => {
            const updateCallback = (type) => updatePatternDisplay(type, patternDisplay);
            populatePoemTypes(poemNation.value, poemTypeSelect, updateCallback, !isRestoringState);
            
            if (!isRestoringState) {
                saveSelectionState(poemNation.value, poemTypeSelect.value);
            }
        });
    }
    
    // Event listener per cambio tipo poesia
    if (poemTypeSelect) {
        poemTypeSelect.addEventListener('change', () => {
            const selectedType = poemTypeSelect.value;
            console.log('Cambio tipo poesia a:', selectedType);
            
            updatePatternDisplay(selectedType, patternDisplay);
            
            // Aggiorna placeholder del textarea
            if (poemText) {
                if (selectedType === 'versi_liberi') {
                    poemText.placeholder = "Non ti ferma più nessuno!!";
                } else {
                    poemText.placeholder = "Scrivi qui i tuoi versi :3";
                }
            }
            
            // Animazione
            poemTypeSelect.classList.add('animate__pulse');
            setTimeout(() => {
                poemTypeSelect.classList.remove('animate__pulse');
            }, 500);
            
            // Salva stato se non stiamo ripristinando
            if (!isRestoringState) {
                console.log('💾 Salvataggio nuovo stato dopo cambio tipo');
                saveSelectionState(poemNation.value, selectedType);
            }
        });
    }
    
    // Event listeners per focus/blur del textarea
    if (poemText && patternDisplay) {
        poemText.addEventListener('focus', () => {
            poemText.style.borderColor = 'var(--primary)';
            const firstBadge = patternDisplay.querySelector('.badge');
            if (firstBadge) firstBadge.classList.add('pulse');
        });
        
        poemText.addEventListener('blur', () => {
            poemText.style.borderColor = '';
        });
        
        // Event listener per input del textarea
        poemText.addEventListener('input', (e) => {
            handlePoemTextInput(e, poemTypeSelect);
        });
    }
    
    // Event listener per checkbox pubblicazione
    if (publishCheckbox) {
        publishCheckbox.addEventListener('change', () => {
            handlePublishToggle(publishCheckbox.checked);
        });
    }
    
    // Gestione invio tramite bottone, evitando submit nativo
    const submitBtn = document.getElementById('submitBtn');
    if (submitBtn) {
        submitBtn.addEventListener('click', (e) => {
            e.preventDefault();
            handleFormSubmit(e, elements);
        });
    }
    
    // Event listener per bottone copia
    if (copyBtn && poemText) {
        copyBtn.addEventListener('click', async () => {
            const textVal = poemText.value || '';
            const trimmed = textVal.trim();
            // REQUIREMENT: mostrare anche toast di errore quando l'utente prova a copiare testo vuoto.
            if (!trimmed) {
                let emptyIssues = validateCurrentInput({
                    text: textVal,
                    poemType: poemTypeSelect?.value,
                    action: 'copy',
                    publishChecked: publishCheckbox?.checked,
                    authorValue: document.getElementById('poemAuthor')?.value || ''
                })
                // Filtra warning ridondanti collegati al vuoto (non servono se mostriamo il toast)
                .filter(i => !['PUBLISH_NO_AUTHOR_ASSIGNED','INPUT_EMPTY','COPY_EMPTY'].includes(i.code));
                const alreadyHasError = emptyIssues.some(i => i.severity === 'error');
                if (!alreadyHasError) {
                    emptyIssues = [
                        ...emptyIssues,
                        { code: 'COPY_EMPTY_ERROR', severity: 'error', message: 'Nulla da copiare: inserisci prima qualche verso.', blockingActions:{ copy:true } }
                    ];
                }
                renderIssues(emptyIssues);
                return; // STOP: nessun tentativo di copia
            }
            const issues = validateCurrentInput({
                text: textVal,
                poemType: poemTypeSelect?.value,
                action: 'copy',
                publishChecked: publishCheckbox?.checked,
                authorValue: document.getElementById('poemAuthor')?.value || ''
            });
            renderIssues(issues.filter(i=>i.code!=='PUBLISH_NO_AUTHOR_ASSIGNED'));
            const success = await copyToClipboard(textVal);
            if (success) {
                vibrate(7);
                showBootstrapToast('copyToast');
            } else {
                // Nessun alert: solo messaggio informativo
                const container = document.getElementById('validationMessages');
                const existing = container?.querySelector('[data-code="COPY_FALLBACK"]');
                if (!existing) {
                    renderIssues([
                        ...issues,
                        { code:'COPY_FALLBACK', severity:'info', message:'Copia non supportata: seleziona e copia manualmente.', blockingActions:{} }
                    ]);
                }
            }
        });
    }
    
    // Animazioni per il selettore tipo poesia
    if (poemTypeSelect) {
        poemTypeSelect.addEventListener('mouseenter', () => {
            poemTypeSelect.style.transform = 'translateY(-2px)';
        });
        
        poemTypeSelect.addEventListener('mouseleave', () => {
            poemTypeSelect.style.transform = 'translateY(0)';
        });
    }
}

/**
 * Inizializza l'applicazione con valori di default e ripristino stato
 * @param {Object} elements - Elementi DOM
 */
function initializeApplication(elements) {
    const { poemNation, poemTypeSelect, patternDisplay, poemText, publishCheckbox } = elements;
    
    console.log('🔧 Inizializzazione applicazione');
    
    // Attach validation handlers early
    attachValidationHandlers(elements);

    // Impostazioni iniziali basate sullo stato attuale del DOM (non sovrascrivere scelte utente)
    const currentNation = poemNation.value || 'giapponesi';
    const updateCallback = (type) => updatePatternDisplay(type, patternDisplay);

    // Popola il select dei tipi in base alla nazione corrente
    populatePoemTypes(currentNation, poemTypeSelect, updateCallback, false);

    // Mantieni il tipo attuale se presente; altrimenti fallback sensato
    const currentType = poemTypeSelect.value || (currentNation === 'giapponesi' ? 'haiku' : (currentNation === 'italiane' ? 'sonetto' : 'limerick'));
    poemTypeSelect.value = currentType;
    updatePatternDisplay(currentType, patternDisplay);
    
    // Tentativo di ripristino stato
    try {
        isRestoringState = true;
        const savedState = restoreSelectionState(poemTypes);
        
        if (savedState) {
            console.log('✅ Ripristino stato trovato:', savedState);
            
            // Applica stato ripristinato
            poemNation.value = savedState.nation;
            populatePoemTypes(savedState.nation, poemTypeSelect, updateCallback, false);
            poemTypeSelect.value = savedState.type;
            updatePatternDisplay(savedState.type, patternDisplay);
            
            if (savedState.partial) {
                console.log('⚠️ Ripristino parziale completato');
            }
        } else {
            console.log('📭 Nessuno stato salvato, uso defaults');
        }
    } catch (e) {
        console.warn('❌ Errore durante il ripristino:', e);
    } finally {
        isRestoringState = false;
        console.log('✅ Inizializzazione completata');
    }
}

// Esporta funzioni per debugging e testing
window.PoetryApp = {
    updatePatternDisplay: (type, element) => updatePatternDisplay(type, element),
    saveState: saveSelectionState,
    restoreState: restoreSelectionState,
    showResults,
    poemTypes,
    isRestoringState: () => isRestoringState,
    validate: (action='manual') => {
        const els = getDOMElements();
        const issues = validateCurrentInput({
            text: els.poemText?.value || '',
            poemType: els.poemTypeSelect?.value,
            action,
            publishChecked: els.publishCheckbox?.checked,
            authorValue: document.getElementById('poemAuthor')?.value || ''
        });
        renderIssues(issues);
        return issues;
    },
    markAnalysisCompleted
};

console.log('📚 Poetry Analyzer App - Versione modulare caricata');
