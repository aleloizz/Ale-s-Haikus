/**
 * @fileoverview Gestione del localStorage per la persistenza dello stato
 * @author Poetry Analyzer App
 */

const STORAGE_KEY = 'poemSelectionState';

/**
 * Salva lo stato della selezione nel localStorage
 * @param {string} nation - Nazione selezionata
 * @param {string} type - Tipo di poesia selezionato
 */
export function saveSelectionState(nation, type) {
    const state = { nation, type };
    console.log('💾 Salvataggio stato:', state);
    
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        console.log('✅ Stato salvato in localStorage');
    } catch (error) {
        console.warn('❌ Errore nel salvataggio stato:', error);
    }
}

/**
 * Ripristina lo stato della selezione dal localStorage
 * @param {Object} poemTypes - Oggetto con i tipi di poesia disponibili
 * @returns {Object|null} Stato ripristinato o null se non trovato/invalido
 */
export function restoreSelectionState(poemTypes) {
    console.log('🔄 restoreSelectionState() chiamata');
    
    try {
        const saved = localStorage.getItem(STORAGE_KEY);
        console.log('💾 Stato salvato trovato:', saved);
        
        if (!saved) {
            console.log('📭 Nessuno stato salvato trovato');
            return null;
        }

        const state = JSON.parse(saved);
        console.log('📋 Stato parsed:', state);
        
        // Verifica che la nazione sia valida
        if (!state.nation || !poemTypes[state.nation]) {
            console.log('⚠️ Nazione non valida nel localStorage');
            return null;
        }

        console.log('🌍 Tentativo ripristino nazione:', state.nation);
        
        // Verifica che il tipo sia valido per questa nazione
        if (!state.type || !poemTypes[state.nation].some(pt => pt.value === state.type)) {
            console.log('⚠️ Tipo non valido per nazione, ripristino solo nazione');
            // Ritorna stato parzialmente valido con primo tipo della nazione
            return {
                nation: state.nation,
                type: poemTypes[state.nation][0].value,
                partial: true
            };
        }

        console.log('✅ Ripristino completo - Nazione:', state.nation, 'Tipo:', state.type);
        return {
            nation: state.nation,
            type: state.type,
            partial: false
        };
        
    } catch (e) {
        console.warn('❌ Errore nel ripristino stato:', e);
        return null;
    }
}

/**
 * Rimuove lo stato salvato dal localStorage
 */
export function clearSelectionState() {
    try {
        localStorage.removeItem(STORAGE_KEY);
        console.log('🗑️ Stato rimosso dal localStorage');
    } catch (error) {
        console.warn('❌ Errore nella rimozione stato:', error);
    }
}

/**
 * Verifica se esiste uno stato salvato nel localStorage
 * @returns {boolean} True se esiste uno stato salvato
 */
export function hasStoredState() {
    try {
        const saved = localStorage.getItem(STORAGE_KEY);
        return saved !== null;
    } catch (error) {
        console.warn('❌ Errore nella verifica stato:', error);
        return false;
    }
}
