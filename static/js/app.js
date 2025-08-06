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
    // Elementi UI esistenti
    const poemNation = document.getElementById('poemNation');
    const poemTypeSelect = document.getElementById('poemType');
    const patternDisplay = document.getElementById('patternDisplay');
    const poemText = document.getElementById('poemText');
    const poemForm = document.getElementById('poemForm');
    const copyBtn = document.getElementById('copyBtn');

    // NUOVI ELEMENTI PER LA BACHECA
    const publishCheckbox = document.getElementById('publishPoem');
    const publishFields = document.getElementById('publishFields');
    const submitBtnText = document.getElementById('submitBtnText');

    // Limite di caratteri lato frontend
    poemText.setAttribute('maxlength', 500);

    // Funzione di sanitizzazione base (rimuove tag HTML)
    function sanitizeInput(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // FUNZIONI PER SALVARE/RIPRISTINARE LO STATO
    function saveSelectionState() {
        const state = {
            nation: poemNation.value,
            type: poemTypeSelect.value
        };
        console.log('💾 Salvataggio stato:', state);
        localStorage.setItem('poemSelectionState', JSON.stringify(state));
        console.log('✅ Stato salvato in localStorage');
    }

    function restoreSelectionState() {
        console.log('🔄 restoreSelectionState() chiamata');
        try {
            const saved = localStorage.getItem('poemSelectionState');
            console.log('💾 Stato salvato trovato:', saved);
            
            if (saved) {
                const state = JSON.parse(saved);
                console.log('📋 Stato parsed:', state);
                
                // Verifica che la nazione sia valida
                if (state.nation && poemTypes[state.nation]) {
                    console.log('🌍 Tentativo ripristino nazione:', state.nation);
                    
                    // Verifica che il tipo sia valido per questa nazione
                    if (state.type && poemTypes[state.nation].some(pt => pt.value === state.type)) {
                        console.log('✅ Ripristino completo - Nazione:', state.nation, 'Tipo:', state.type);
                        
                        // Imposta nazione e popola tipi
                        poemNation.value = state.nation;
                        populatePoemTypes(state.nation);
                        
                        // Imposta tipo e aggiorna badge
                        poemTypeSelect.value = state.type;
                        updatePatternDisplay(state.type);
                        
                        return true; // Stato ripristinato con successo
                    } else {
                        console.log('⚠️ Tipo non valido per nazione, ripristino solo nazione');
                        poemNation.value = state.nation;
                        populatePoemTypes(state.nation);
                        // Lascia che il primo tipo della lista venga selezionato automaticamente
                        const firstType = poemTypes[state.nation][0].value;
                        poemTypeSelect.value = firstType;
                        updatePatternDisplay(firstType);
                        return true; // Ripristino parziale ma valido
                    }
                } else {
                    console.log('⚠️ Nazione non valida nel localStorage');
                }
            } else {
                console.log('📭 Nessuno stato salvato trovato');
            }
        } catch (e) {
            console.warn('❌ Errore nel ripristino stato:', e);
        }
        
        console.log('🔄 Fallback a stato di default (haiku)');
        return false; // Fallback a stato di default
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
        
        // Solo scatena l'evento change se non stiamo ripristinando lo stato
        if (!isRestoringState) {
            poemTypeSelect.dispatchEvent(new Event('change'));
        }
    }

    // Flag per evitare loop durante il ripristino
    let isRestoringState = false;

    poemNation.addEventListener('change', () => {
        populatePoemTypes(poemNation.value);
        if (!isRestoringState) {
            saveSelectionState();
        }
    });

    // NUOVO ORDINE DI INIZIALIZZAZIONE - RESET COMPLETO PER COERENZA
    console.log('🚀 Inizializzazione app - reset completo per coerenza');
    
    // 1. Reset al default: giapponesi -> haiku
    poemNation.value = 'giapponesi';
    populatePoemTypes('giapponesi');
    poemTypeSelect.value = 'haiku';
    
    // 2. Prova a ripristinare lo stato salvato (se esiste)
    isRestoringState = true;
    const stateRestored = restoreSelectionState();
    isRestoringState = false;
    
    // 3. Se il ripristino fallisce, assicurati che sia tutto coerente con haiku
    if (!stateRestored) {
        console.log('📋 Nessuno stato ripristinato - mantieni coerenza haiku');
        poemNation.value = 'giapponesi';
        populatePoemTypes('giapponesi');
        poemTypeSelect.value = 'haiku';
    }
    
    // 4. Inizializza i badge con lo stato finale
    const finalType = poemTypeSelect.value;
    console.log('🎯 Tipo finale per badge:', finalType);
    initBadges();
    
    // 5. Controllo finale per assicurare coerenza
    setTimeout(() => {
        const currentNation = poemNation.value;
        const currentType = poemTypeSelect.value;
        console.log('🔍 Controllo finale - Nazione:', currentNation, 'Tipo:', currentType);
        
        // Verifica che il tipo sia valido per la nazione corrente
        const typeExists = poemTypes[currentNation] && 
                          poemTypes[currentNation].some(pt => pt.value === currentType);
        
        if (!typeExists) {
            console.log('⚠️ Tipo inconsistente! Reset forzato a haiku');
            poemNation.value = 'giapponesi';
            populatePoemTypes('giapponesi');
            poemTypeSelect.value = 'haiku';
            updatePatternDisplay('haiku');
        } else {
            updatePatternDisplay(currentType);
        }
        
        console.log('✅ Inizializzazione completa');
    }, 200);
   
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
        console.log('🎯 updatePatternDisplay() chiamata con tipo:', type);
        
        const pattern = patterns[type];
        if (!pattern) {
            console.warn('⚠️ Pattern non trovato per tipo:', type);
            return;
        }

        console.log('📋 Pattern trovato:', pattern);

        if (type === 'versi_liberi') {
            patternDisplay.innerHTML = `
                <span class="badge bg-haiku-secondary syllable-badge">Nessun vincolo metrico</span>
                <div class="mt-2 small text-muted">
                    Libera la tua creatività, ogni verso sarà analizzato per sillabe e rime.
                </div>
            `;
            console.log('✅ Pattern "versi liberi" applicato');
            return;
        }

        let html = pattern.syllables.map(count => `
            <span class="badge bg-haiku-secondary syllable-badge">${count}</span>
        `).join('');

        // MOSTRA LE RIME SOLO SE IL TIPO DI POESIA LE RICHIEDE
        if (pattern.rhyme && pattern.rhyme !== null) {
            html += `<div class="mt-2 rhyme-pattern small text-muted">
                    <i class="bi bi-music-note-beamed"></i> Schema: ${pattern.rhyme.join(' ')}
                </div>`;
        }

        patternDisplay.innerHTML = html;
        console.log('✅ Pattern HTML aggiornato:', html.substring(0, 100) + '...');
    }

    // Inizializza i badge
    function initBadges() {
        console.log('🔧 initBadges() chiamata');
        
        // Verifica che gli elementi esistano
        if (!patternDisplay) {
            console.error('❌ Elemento patternDisplay non trovato!');
            return;
        }
        
        if (!poemTypeSelect) {
            console.error('❌ Elemento poemTypeSelect non trovato!');
            return;
        }
        
        // Usa il tipo attualmente selezionato
        const currentType = poemTypeSelect.value;
        console.log('📊 initBadges - Tipo corrente dal select:', currentType);
        
        // Se non c'è un tipo selezionato, usa haiku come default
        const typeToUse = currentType || 'haiku';
        console.log('🎯 initBadges - Tipo da usare:', typeToUse);
        
        updatePatternDisplay(typeToUse);
        
        // Assicurati che il select abbia il valore corretto
        if (!currentType) {
            poemTypeSelect.value = 'haiku';
            console.log('🔧 Select forzato a haiku per coerenza');
        }
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
        console.log('🎛️ Cambio tipo poesia a:', selectedType);
        
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
        
        // Salva lo stato quando cambia il tipo (solo se non stiamo ripristinando)
        if (!isRestoringState) {
            console.log('💾 Salvataggio nuovo stato dopo cambio tipo');
            saveSelectionState();
        }
    });

    // GESTIONE CHECKBOX PUBBLICAZIONE (NUOVA)
    if (publishCheckbox) {
        publishCheckbox.addEventListener('change', () => {
            if (publishCheckbox.checked) {
                publishFields.style.display = 'block';
                publishFields.style.animation = 'fadeIn 0.3s ease';
                if (submitBtnText) submitBtnText.textContent = 'Verifica e Pubblica';
            } else {
                publishFields.style.display = 'none';
                if (submitBtnText) submitBtnText.textContent = 'Verifica';
            }
        });
    }

    // FORM SUBMIT MODIFICATO (sostituisce quello esistente)
    poemForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
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
            
            // Se deve pubblicare e l'analisi è completata (anche se non valida)
            if (shouldPublish && !data.error) {
                await publishPoem({
                    text: sanitizedText,
                    poem_type: poemTypeSelect.value,
                    title: document.getElementById('poemTitle')?.value.trim() || '',
                    author: document.getElementById('poemAuthor')?.value.trim() || 'Poeta Anonimo'
                }, data.valid);
            }
            
        } catch (error) {
            console.error('Error:', error);
            showResults({
                error: true,
                message: error.message
            });
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
        }
    });

    // NUOVE FUNZIONI PER LA PUBBLICAZIONE
    async function publishPoem(formData, isValid) {
        try {
            const useTolerance = document.getElementById('useTolerance')?.checked || false;
            
            const publishResponse = await fetch('/api/poems', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: formData.text,
                    poem_type: formData.poem_type,
                    title: formData.title,
                    author: formData.author,
                    use_tolerance: useTolerance
                })
            });
            
            const publishData = await publishResponse.json();
            
            if (publishData.success) {
                showPublishSuccess();
            } else {
                // Gestisci errori di metrica con dettagli
                if (publishData.details && publishData.details.length > 0) {
                    showPublishError(publishData.message, publishData.details);
                } else {
                    showPublishError(publishData.message || 'Errore nella pubblicazione');
                }
            }
            
        } catch (error) {
            console.error('Errore pubblicazione:', error);
            showPublishError('Errore nella pubblicazione. Riprova più tardi.');
        }
    }
    
    function showPublishSuccess() {
        const toastContainer = document.querySelector('.toast-container');
        const successToast = document.createElement('div');
        successToast.className = 'toast show';
        successToast.setAttribute('role', 'alert');
        successToast.innerHTML = `
            <div class="toast-header bg-success text-white">
                <i class="bi bi-check-circle-fill me-2"></i>
                <strong class="me-auto">Pubblicazione riuscita!</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                🎉 La tua poesia è stata pubblicata con successo! 
                <div class="mt-2">
                    <a href="/bacheca" class="btn btn-sm btn-outline-primary">
                        <i class="bi bi-collection"></i> Visualizza nella bacheca
                    </a>
                </div>
            </div>
        `;
        
        toastContainer.appendChild(successToast);
        
        setTimeout(() => {
            if (successToast.parentNode) {
                successToast.remove();
            }
        }, 8000);
        
        // Reset form di pubblicazione
        if (publishCheckbox) {
            publishCheckbox.checked = false;
            publishFields.style.display = 'none';
            if (submitBtnText) submitBtnText.textContent = 'Verifica';
        }
        
        const titleField = document.getElementById('poemTitle');
        const authorField = document.getElementById('poemAuthor');
        if (titleField) titleField.value = '';
        if (authorField) authorField.value = 'Poeta Anonimo';
    }
    
    // Modifica showPublishError per mostrare dettagli
    function showPublishError(message, details = null) {
        const toastContainer = document.querySelector('.toast-container');
        const errorToast = document.createElement('div');
        errorToast.className = 'toast show';
        errorToast.setAttribute('role', 'alert');
        
        let detailsHtml = '';
        if (details && details.length > 0) {
            detailsHtml = `
                <div class="mt-2">
                    <small class="text-muted">Dettagli:</small>
                    <ul class="mb-0 small">
                        ${details.map(detail => `<li>${detail}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        errorToast.innerHTML = `
            <div class="toast-header bg-danger text-white">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                <strong class="me-auto">Pubblicazione non consentita</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
                ${detailsHtml}
                <div class="mt-2">
                    <small class="text-muted">💡 Correggi la poesia e riprova!</small>
                </div>
            </div>
        `;
        
        toastContainer.appendChild(errorToast);
        
        setTimeout(() => {
            if (errorToast.parentNode) {
                errorToast.remove();
            }
        }, 8000); // Più tempo per leggere i dettagli
    }

    // Animazione selettore tipo poesia
    poemTypeSelect.addEventListener('mouseenter', () => {
        poemTypeSelect.style.transform = 'translateY(-2px)';
    });

    poemTypeSelect.addEventListener('mouseleave', () => {
        poemTypeSelect.style.transform = 'translateY(0)';
    });

    // Mostra risultati (MODIFICA LA FUNZIONE ESISTENTE)
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

        // CONTROLLO SE IL TIPO DI POESIA RICHIEDE RIME
        const currentPoemPattern = patterns[data.poem_type];
        const requiresRhymes = currentPoemPattern && currentPoemPattern.rhyme !== null;
        
        // Analisi rime SOLO se il tipo di poesia lo richiede
        if (requiresRhymes && data.rhyme_analysis) {
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

    // Funzioni di supporto esistenti (invariate)
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
    
    function analyzeRhymeStatus(data) {
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

    function estrai_ultime_sillabe(versoObj, n = 2) {
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

    // Copia testo (invariato)
    copyBtn.addEventListener('click', async () => {
        try {
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(poemText.value);
            } else {
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