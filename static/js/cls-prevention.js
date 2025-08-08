/**
 * @fileoverview Pre-inizializzazione immediata per prevenire CLS su desktop
 * Questo script deve essere eseguito inline per evitare layout shift
 * @author Poetry Analyzer App
 */

(function() {
    'use strict';
    
    // Esegui solo su desktop per non interferire con mobile
    if (window.innerWidth < 992) return;
    
    // Attendi che il DOM sia pronto
    function initCLSPrevention() {
        // Stabilizza immediatamente le dimensioni della card principale
        const card = document.querySelector('.card');
        if (card) {
            card.style.minHeight = '700px';
            card.style.width = '600px';
            card.style.maxWidth = '600px';
            card.style.contain = 'layout style';
        }
        
        // Stabilizza il pattern display
        const patternDisplay = document.getElementById('patternDisplay');
        if (patternDisplay) {
            patternDisplay.style.height = '60px';
            patternDisplay.style.minHeight = '60px';
            patternDisplay.style.contain = 'strict';
        }
        
        // Stabilizza il container dei selettori
        const formSelectContainer = document.querySelector('.form-select-container');
        if (formSelectContainer) {
            formSelectContainer.style.height = '140px';
            formSelectContainer.style.minHeight = '140px';
            formSelectContainer.style.contain = 'layout';
        }
        
        // Stabilizza il textarea
        const poemText = document.getElementById('poemText');
        if (poemText) {
            poemText.style.height = '150px';
            poemText.style.minHeight = '150px';
            poemText.style.contain = 'layout';
        }
        
        // Stabilizza il main
        const main = document.querySelector('main');
        if (main) {
            main.style.minHeight = 'calc(100vh - 320px)';
            main.style.contain = 'layout';
        }
        
        console.log('🛡️ CLS Prevention: Elementi stabilizzati per desktop');
    }
    
    // Esegui immediatamente se il DOM è già pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCLSPrevention, { once: true });
    } else {
        initCLSPrevention();
    }
})();
