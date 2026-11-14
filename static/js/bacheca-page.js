/**
 * Inizializzazione della pagina bacheca.
 *
 * Tutto il codice che prima era inline è qui: la CSP non richiede eccezioni
 * per handler o script inline e i dati dinamici vengono scritti con
 * textContent, mai con innerHTML.
 */
import { getCsrfToken } from './utils.js?v=1.4.0';

const configElement = document.getElementById('bacheca-config');
window.BACHECA_CONFIG = configElement
    ? JSON.parse(configElement.textContent)
    : { currentPage: 1, totalPages: 1, itemsPerPage: 12, filters: {}, sortBy: 'recent', baseUrl: '/bacheca' };

function initDropdowns() {
    if (!window.bootstrap || !bootstrap.Dropdown) return;
    document.querySelectorAll('[data-bs-toggle="dropdown"]').forEach((toggle) => {
        try {
            bootstrap.Dropdown.getOrCreateInstance(toggle);
        } catch (err) {
            console.warn('Dropdown non inizializzato:', err);
        }
    });
}

function initFilterResetButtons() {
    document.querySelectorAll('.js-clear-filter').forEach((button) => {
        button.addEventListener('click', () => {
            const targetId = button.getAttribute('data-filter-target');
            const eventName = button.getAttribute('data-filter-event') || 'change';
            const target = targetId ? document.getElementById(targetId) : null;
            if (!target) return;
            target.value = '';
            target.dispatchEvent(new Event(eventName, { bubbles: true }));
        });
    });
}

function initReloadButton() {
    const reload = document.querySelector('[data-action="reload"]');
    if (reload) {
        reload.addEventListener('click', () => window.location.reload());
    }
}

async function postJson(url) {
    return fetch(url, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: '{}'
    });
}

function initHeartLikes() {
    document.querySelectorAll('.like-container[data-poem-id]').forEach((container) => {
        if (container.dataset.likeBound === 'true') return;
        container.dataset.likeBound = 'true';

        const checkbox = container.querySelector('.heart-container .checkbox');
        const countElement = container.querySelector('.like-count');
        if (!checkbox) return;

        // Il contenitore è cliccabile ma il click sul checkbox non deve
        // generare un doppio evento.
        container.addEventListener('click', (event) => {
            if (event.target !== checkbox) checkbox.click();
        });

        checkbox.addEventListener('change', async () => {
            const poemId = container.getAttribute('data-poem-id');
            const liked = checkbox.checked;
            const url = liked
                ? `/api/poems/${poemId}/like`
                : `/api/poems/${poemId}/unlike`;
            try {
                const response = await postJson(url);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                const data = await response.json();
                if (!data.success) throw new Error(data.error || 'Errore sconosciuto');
                if (countElement && typeof data.likes === 'number') {
                    countElement.textContent = String(data.likes);
                }
                if (typeof data.liked === 'boolean') {
                    checkbox.checked = data.liked;
                }
            } catch (err) {
                console.error('Errore toggle like:', err);
                checkbox.checked = !liked;
            }
        });
    });
}

async function syncHeartLikeStatus() {
    const containers = document.querySelectorAll('.like-container[data-poem-id]');
    await Promise.all(
        Array.from(containers).map(async (container) => {
            const poemId = container.getAttribute('data-poem-id');
            if (!poemId) return;
            try {
                const response = await fetch(`/api/poems/${poemId}/like/status`, {
                    credentials: 'same-origin'
                });
                if (!response.ok) return;
                const data = await response.json();
                if (!data.success) return;
                const checkbox = container.querySelector('.heart-container .checkbox');
                const countElement = container.querySelector('.like-count');
                if (checkbox && typeof data.liked === 'boolean') {
                    checkbox.checked = data.liked;
                }
                if (countElement && typeof data.likes === 'number') {
                    countElement.textContent = String(data.likes);
                }
            } catch (err) {
                console.debug('Stato like non disponibile per', poemId);
            }
        })
    );
}

async function loadBachecaModule() {
    try {
        await import('./bacheca.js?v=1.12');
    } catch (err) {
        console.warn('Modulo bacheca non disponibile:', err);
    }
    window.goToSpecificPage = () => {
        if (window.bachecaManager) return window.bachecaManager.goToSpecificPage();
        const pageInput = document.getElementById('goToPage');
        const page = pageInput ? parseInt(pageInput.value, 10) : NaN;
        const total = Number(window.BACHECA_CONFIG?.totalPages || 1);
        if (!Number.isFinite(page) || page < 1 || page > total) {
            window.alert('Numero pagina non valido');
            return;
        }
        const params = new URLSearchParams(window.location.search);
        params.set('page', String(page));
        window.location.href = `${window.location.pathname}?${params.toString()}`;
    };
    window.expandPoem = (id) => {
        if (window.bachecaManager) return window.bachecaManager.expandPoem(id);
        const modal = document.getElementById('expandedPoemModal');
        if (modal && window.bootstrap && bootstrap.Modal) {
            bootstrap.Modal.getOrCreateInstance(modal).show();
        }
    };
}

function init() {
    initDropdowns();
    initFilterResetButtons();
    initReloadButton();
    initHeartLikes();
    syncHeartLikeStatus();
    loadBachecaModule();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
} else {
    init();
}
