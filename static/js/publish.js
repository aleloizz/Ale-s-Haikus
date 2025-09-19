/**
 * @fileoverview Gestione della pubblicazione delle poesie e notifiche toast
 * @author Poetry Analyzer App
 */

/**
 * Pubblica una poesia sul server
 * @param {Object} formData - Dati del form di pubblicazione
 * @param {boolean} isValid - Se la poesia è metricamente valida
 * @returns {Promise<void>}
 */
export async function publishPoem(formData, isValid) {
    try {
        // Client-side guard: non inviare se già sappiamo che è invalida
        if (isValid === false) {
            const typeLabel = formData.poem_type ? `Tipo selezionato: ${formData.poem_type}` : null;
            showPublishError(
                'Pubblicazione non consentita: la poesia non rispetta i vincoli metrici.',
                [typeLabel].filter(Boolean)
            );
            return;
        }
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
                const message = publishData.message || publishData.error || 'Errore nella pubblicazione';
                showPublishError(message);
            }
        }
        
    } catch (error) {
        console.error('Errore pubblicazione:', error);
        showPublishError('Errore nella pubblicazione. Riprova più tardi.');
    }
}

/**
 * Mostra toast di successo per pubblicazione avvenuta
 */
export function showPublishSuccess() {
    const toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        console.warn('⚠️ Toast container non trovato');
        return;
    }
    
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
    
    // Rimuovi il toast dopo 8 secondi
    setTimeout(() => {
        if (successToast.parentNode) {
            successToast.remove();
        }
    }, 8000);
    
    // Reset form di pubblicazione
    resetPublishForm();
}

/**
 * Mostra toast di errore per pubblicazione fallita
 * @param {string} message - Messaggio di errore
 * @param {Array<string>} details - Dettagli dell'errore (opzionale)
 */
export function showPublishError(message, details = null) {
    const toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        console.warn('⚠️ Toast container non trovato');
        return;
    }
    
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
    
    // Rimuovi il toast dopo 8 secondi (più tempo per leggere i dettagli)
    setTimeout(() => {
        if (errorToast.parentNode) {
            errorToast.remove();
        }
    }, 8000);
}

/**
 * Resetta il form di pubblicazione dopo una pubblicazione riuscita
 */
function resetPublishForm() {
    const publishCheckbox = document.getElementById('publishPoem');
    const publishFields = document.getElementById('publishFields');
    const submitBtnText = document.getElementById('submitBtnText');
    
    if (publishCheckbox) {
        publishCheckbox.checked = false;
        
        if (publishFields) {
            publishFields.style.display = 'none';
        }
        
        if (submitBtnText) {
            submitBtnText.textContent = 'Verifica';
        }
    }
    
    // Reset campi del form
    const titleField = document.getElementById('poemTitle');
    const authorField = document.getElementById('poemAuthor');
    
    if (titleField) titleField.value = '';
    if (authorField) authorField.value = 'Poeta Anonimo';
}

/**
 * Gestisce il toggle della checkbox di pubblicazione
 * @param {boolean} isChecked - Stato della checkbox
 */
export function handlePublishToggle(isChecked) {
    const publishFields = document.getElementById('publishFields');
    const submitBtnText = document.getElementById('submitBtnText');
    
    if (isChecked) {
        if (publishFields) {
            // Use height animation to prevent CLS
            publishFields.style.display = 'block';
            publishFields.style.height = 'auto';
            const targetHeight = publishFields.scrollHeight + 'px';
            publishFields.style.height = '0px';
            publishFields.offsetHeight; // Force reflow
            publishFields.style.height = targetHeight;
            publishFields.style.opacity = '1';
        }
        if (submitBtnText) {
            submitBtnText.textContent = 'Verifica e Pubblica';
        }
    } else {
        if (publishFields) {
            publishFields.style.height = '0px';
            publishFields.style.opacity = '0';
            setTimeout(() => {
                if (publishFields.style.height === '0px') {
                    publishFields.style.display = 'none';
                }
            }, 300); // Match CSS transition duration
        }
        if (submitBtnText) {
            submitBtnText.textContent = 'Verifica';
        }
    }
}
