/**
 * Bacheca delle Poesie - JavaScript Module
 * Gestisce l'interfaccia interattiva della bacheca poetica
 * @version 1.10 - Aggiunto supporto condivisione social
 */

class BachecaManager {
    constructor() {
        this.currentFilters = {
            search: '',
            type: 'all',
            author: 'all',
            valid_only: false
        };
        
        this.currentSort = 'recent';
        this.currentPage = 1;
        this.totalPages = 1;
        this.isLoading = false;
        
        // Cache elementi DOM
        this.elements = {};
        this.toasts = {};
        
        // Debounce timers
        this.searchTimeout = null;
        
        // Configurazione
        this.config = {
            searchDelay: 500,
            animationDuration: 300,
            loadingTimeout: 10000,
            share: {
                origin: typeof window !== 'undefined' ? window.location.origin : '',
                // Future-proof: modify here if permalink pattern changes
                permalinkPattern: (id) => `/poesia/${id}`,
                defaultShareText: "Guarda questa poesia su Ale's Haikus"
            }
        };

        // Share popup state
        this.shareState = {
            activePoemId: null,
            overlay: null,
            popup: null,
            extra: null,
            closeBtn: null
        };

        // Stato navigazione modal espansa
        this.expandedState = {
            ids: [],        // ordered list of visible poem ids
            currentIndex: -1,
            isOpen: false
        };
    }

    /**
     * Inizializza il manager della bacheca
     */
    init() {
        this.cacheElements();
        this.initializeEventListeners();
        this.initializeToasts();
    this.initializeSharePopup();
        this.loadSavedPreferences();
        this.updateUI();
        
        console.log('BachecaManager inizializzato');
    }

    /**
     * Cache degli elementi DOM per performance
     */
    cacheElements() {
        this.elements = {
            // Filtri
            searchText: document.getElementById('searchText'),
            typeFilter: document.getElementById('typeFilter'),
            authorFilter: document.getElementById('authorFilter'),
            onlyValidFilter: document.getElementById('onlyValidFilter'),
            applyFilters: document.getElementById('applyFilters'),
            clearFilters: document.getElementById('clearFilters'),
            clearAllFilters: document.getElementById('clearAllFilters'),
            
            // Container e controlli
            poemsContainer: document.getElementById('poemsContainer'),
            loadingIndicator: document.getElementById('loadingIndicator'),
            poemCount: document.getElementById('poemCount'),
            
            // Vista
            viewGrid: document.getElementById('viewGrid'),
            viewList: document.getElementById('viewList'),
            
            // Ordinamento
            sortButtons: document.querySelectorAll('[data-sort]'),
            
            // Paginazione
            goToPage: document.getElementById('goToPage'),
            
            // Modal
            expandedModal: document.getElementById('expandedPoemModal'),
            expandedTitle: document.getElementById('expandedPoemTitle'),
            expandedContent: document.getElementById('expandedPoemContent'),
            expandedAuthor: document.getElementById('expandedPoemAuthor'),
            expandedInfo: document.getElementById('expandedPoemInfo'),
            expandedCopyBtn: document.getElementById('expandedCopyBtn'),
            expandedLikeBtn: document.getElementById('expandedLikeBtn'),
            expandedLikeCount: document.getElementById('expandedLikeCount')
        };
    }

    /**
     * Inizializza tutti gli event listeners
     */
    initializeEventListeners() {
        // Filtri
        this.setupFilterListeners();
        
        // Vista
        this.setupViewListeners();
        
        // Azioni delle card
        this.setupActionButtons();
        
        // Ordinamento
        this.setupSortListeners();
        
        // Paginazione
        this.setupPaginationListeners();
        
        // Tasti di scelta rapida
        this.setupKeyboardShortcuts();
        
        // Eventi finestra
        this.setupWindowEvents();
    }

    /**
     * Setup listeners per i filtri
     */
    setupFilterListeners() {
        // Ricerca con debounce
        if (this.elements.searchText) {
            this.elements.searchText.addEventListener('input', (e) => {
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => {
                    this.currentFilters.search = e.target.value.trim();
                    this.applyFilters();
                }, this.config.searchDelay);
            });
        }

        // Filtro tipo
        if (this.elements.typeFilter) {
            this.elements.typeFilter.addEventListener('change', (e) => {
                this.currentFilters.type = e.target.value;
                this.applyFilters();
            });
        }

        // Filtro autore
        if (this.elements.authorFilter) {
            this.elements.authorFilter.addEventListener('change', (e) => {
                this.currentFilters.author = e.target.value;
                this.applyFilters();
            });
        }

        // Solo valide
        if (this.elements.onlyValidFilter) {
            this.elements.onlyValidFilter.addEventListener('change', (e) => {
                this.currentFilters.valid_only = e.target.checked;
                this.applyFilters();
            });
        }

        // Pulsanti filtri
        if (this.elements.applyFilters) {
            this.elements.applyFilters.addEventListener('click', () => {
                this.applyFilters();
            });
        }

        if (this.elements.clearFilters) {
            this.elements.clearFilters.addEventListener('click', () => {
                this.clearFilters();
            });
        }

        if (this.elements.clearAllFilters) {
            this.elements.clearAllFilters.addEventListener('click', () => {
                this.clearAllFilters();
            });
        }
    }

    /**
     * Setup listeners per le viste
     */
    setupViewListeners() {
        if (this.elements.viewGrid) {
            this.elements.viewGrid.addEventListener('change', () => {
                if (this.elements.viewGrid.checked) {
                    this.switchView('grid');
                }
            });
        }

        if (this.elements.viewList) {
            this.elements.viewList.addEventListener('change', () => {
                if (this.elements.viewList.checked) {
                    this.switchView('list');
                }
            });
        }
    }

    /**
     * Setup listeners per le azioni delle card
     */
    setupActionButtons() {
        // Rimuovi eventuali listener diretti precedenti (non necessario ora)
        if (!this._delegatedActionsBound) {
            document.addEventListener('click', async (e) => {
                const trigger = e.target.closest('[data-action]');
                if (!trigger) return;

                // Evita di interferire con link esterni reali
                if (trigger.tagName === 'A' && trigger.getAttribute('href') && trigger.getAttribute('href').startsWith('http')) {
                    return;
                }

                const action = trigger.getAttribute('data-action');
                const poemId = trigger.getAttribute('data-poem-id');
                if (!action || !poemId) return;

                e.preventDefault();
                e.stopPropagation();

                await this.handleCardAction(action, poemId, trigger);

                // Chiudi dropdown se l'azione proviene da un menu
                const dropdownMenu = trigger.closest('.dropdown-menu');
                if (dropdownMenu && window.bootstrap && bootstrap.Dropdown) {
                    const toggle = dropdownMenu.previousElementSibling;
                    if (toggle) {
                        const instance = bootstrap.Dropdown.getInstance(toggle) || new bootstrap.Dropdown(toggle);
                        instance.hide();
                    }
                }
            });
            this._delegatedActionsBound = true;
        }
    }

    /**
     * Setup dei pulsanti like
     */
    setupLikeButtons() {
        document.querySelectorAll('.like-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const poemId = btn.dataset.poemId;
                if (poemId) {
                    await this.toggleLike(poemId, btn);
                }
            });
        });
    }

    /**
     * Setup listeners per l'ordinamento
     */
    setupSortListeners() {
        this.elements.sortButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const sortBy = btn.dataset.sort;
                if (sortBy) {
                    this.applySorting(sortBy);
                }
            });
        });
    }

    /**
     * Setup listeners per la paginazione
     */
    setupPaginationListeners() {
        // Input field
        if (this.elements.goToPage) {
            this.elements.goToPage.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.goToSpecificPage();
                }
            });
        }

        // Pulsante vai alla pagina
        const goToPageBtn = document.getElementById('goToPageBtn');
        if (goToPageBtn) {
            goToPageBtn.addEventListener('click', () => {
                this.goToSpecificPage();
            });
        }
    }

    /**
     * Setup scorciatoie da tastiera
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+F per focalizzare la ricerca
            if (e.ctrlKey && e.key === 'f' && this.elements.searchText) {
                e.preventDefault();
                this.elements.searchText.focus();
                this.elements.searchText.select();
            }
            
            // Escape per pulire filtri solo se modal non aperto
            if (e.key === 'Escape' && !this.expandedState.isOpen) {
                this.clearFilters();
            }
            
            // Frecce per navigazione pagine
            if (e.ctrlKey) {
                if (e.key === 'ArrowLeft' && this.currentPage > 1) {
                    e.preventDefault();
                    this.goToPage(this.currentPage - 1);
                } else if (e.key === 'ArrowRight' && this.currentPage < this.totalPages) {
                    e.preventDefault();
                    this.goToPage(this.currentPage + 1);
                }
            }

            // Navigazione poesie dentro modal espansa (senza Ctrl)
            if (this.expandedState.isOpen && !e.ctrlKey) {
                if (e.key === 'ArrowLeft') {
                    e.preventDefault();
                    this.navigateExpanded(-1);
                } else if (e.key === 'ArrowRight') {
                    e.preventDefault();
                    this.navigateExpanded(1);
                }
            }
        });
    }

    /**
     * Setup eventi finestra
     */
    setupWindowEvents() {
        // Resize per layout responsive
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.handleResize();
            }, 250);
        });

        // Gestione back/forward del browser
        window.addEventListener('popstate', (e) => {
            if (e.state && e.state.bacheca) {
                this.loadStateFromHistory(e.state);
            }
        });
    }

    /**
     * Inizializza i toast
     */
    initializeToasts() {
        this.toasts = {
            copy: document.getElementById('copyToast'),
            error: document.getElementById('errorToast'),
            like: document.getElementById('likeToast')
        };
    }

    /**
     * Carica preferenze salvate
     */
    loadSavedPreferences() {
        // Vista salvata
        const savedView = localStorage.getItem('bachecaViewMode') || 'grid';
        this.switchView(savedView);
        
        // Altri filtri salvati se necessario
        const savedFilters = localStorage.getItem('bachecaFilters');
        if (savedFilters) {
            try {
                const filters = JSON.parse(savedFilters);
                this.currentFilters = { ...this.currentFilters, ...filters };
                this.syncFiltersToUI();
            } catch (e) {
                console.warn('Errore nel caricamento filtri salvati:', e);
            }
        }
    }

    /**
     * Sincronizza filtri con UI
     */
    syncFiltersToUI() {
        if (this.elements.searchText) {
            this.elements.searchText.value = this.currentFilters.search;
        }
        if (this.elements.typeFilter) {
            this.elements.typeFilter.value = this.currentFilters.type;
        }
        if (this.elements.authorFilter) {
            this.elements.authorFilter.value = this.currentFilters.author;
        }
        if (this.elements.onlyValidFilter) {
            this.elements.onlyValidFilter.checked = this.currentFilters.valid_only;
        }
    }

    /**
     * Applica i filtri correnti
     */
    async applyFilters() {
        if (this.isLoading) return;
        
        try {
            this.setLoadingState(true);
            
            // Salva filtri
            localStorage.setItem('bachecaFilters', JSON.stringify(this.currentFilters));
            
            // Costruisci URL con parametri
            const params = new URLSearchParams();
            
            if (this.currentFilters.search) {
                params.append('search', this.currentFilters.search);
            }
            if (this.currentFilters.type !== 'all') {
                params.append('tipo', this.currentFilters.type);
            }
            if (this.currentFilters.author !== 'all') {
                params.append('autore', this.currentFilters.author);
            }
            if (this.currentFilters.valid_only) {
                params.append('solo_valide', 'true');
            }
            if (this.currentSort !== 'recent') {
                params.append('sort', this.currentSort);
            }
            
            params.append('page', '1'); // Reset alla prima pagina
            
            // Naviga alla nuova URL
            const newUrl = `${window.location.pathname}?${params.toString()}`;
            
            // Aggiorna history
            history.pushState({
                bacheca: true,
                filters: this.currentFilters,
                sort: this.currentSort,
                page: 1
            }, '', newUrl);
            
            // Ricarica pagina con nuovi parametri
            window.location.href = newUrl;
            
        } catch (error) {
            console.error('Errore nell\'applicazione filtri:', error);
            this.showToast('error', 'Errore nell\'applicazione dei filtri');
        } finally {
            this.setLoadingState(false);
        }
    }

    /**
     * Pulisce tutti i filtri
     */
    clearFilters() {
        this.currentFilters = {
            search: '',
            type: 'all',
            author: 'all',
            valid_only: false
        };
        
        this.syncFiltersToUI();
        localStorage.removeItem('bachecaFilters');
    }

    /**
     * Pulisce tutti i filtri e ricarica
     */
    clearAllFilters() {
        this.clearFilters();
        
        // Naviga alla bacheca pulita
        history.pushState({
            bacheca: true,
            filters: this.currentFilters,
            sort: 'recent',
            page: 1
        }, '', window.location.pathname);
        
        window.location.href = window.location.pathname;
    }

    /**
     * Cambia vista (griglia/lista)
     */
    switchView(mode) {
        const container = this.elements.poemsContainer;
        if (!container) return;

        // Rimuovi classi esistenti
        container.classList.remove('poems-grid', 'poems-list');
        container.classList.add(`poems-${mode}`);
        
        // Aggiorna radio buttons
        if (mode === 'grid' && this.elements.viewGrid) {
            this.elements.viewGrid.checked = true;
        } else if (mode === 'list' && this.elements.viewList) {
            this.elements.viewList.checked = true;
        }
        
        // Salva preferenza
        localStorage.setItem('bachecaViewMode', mode);
        
        // Animazione
        container.style.opacity = '0.7';
        setTimeout(() => {
            container.style.opacity = '1';
        }, 150);
    }

    /**
     * Toggle like su una poesia
     */
    async toggleLike(poemId, btnElement) {
        if (!poemId || !btnElement) return;

        try {
            // Animazione immediata
            btnElement.classList.add('animate-like');
            btnElement.disabled = true;

            const response = await fetch(`/api/poems/${poemId}/like`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                // Aggiorna conteggio
                const countSpan = btnElement.querySelector('.like-count');
                if (countSpan) {
                    countSpan.textContent = data.likes || 0;
                }
                
                // Mostra toast
                this.showToast('like', data.message || 'Grazie per il tuo apprezzamento!');
                
                // Sincronizza con modal se aperto
                if (this.elements.expandedLikeCount) {
                    this.elements.expandedLikeCount.textContent = data.likes || 0;
                }
            } else {
                throw new Error(data.error || 'Errore sconosciuto');
            }
            
        } catch (error) {
            console.error('Errore nel like:', error);
            this.showToast('error', 'Errore nell\'apprezzamento della poesia');
        } finally {
            // Rimuovi animazione e riabilita pulsante
            setTimeout(() => {
                btnElement.classList.remove('animate-like');
                btnElement.disabled = false;
            }, this.config.animationDuration);
        }
    }

    /**
     * Gestisce azioni delle card (copia, condividi, espandi, dettagli)
     */
    async handleCardAction(action, poemId, btnElement) {
        switch (action) {
            case 'copy':
                await this.copyPoemText(poemId);
                break;
            case 'share':
                this.openSharePopup(poemId);
                break;
            case 'expand':
                this.expandPoem(poemId);
                break;
            case 'detail':
                this.showPoemDetails(poemId);
                break;
            default:
                console.warn(`Azione sconosciuta: ${action}`);
        }
    }

    /**
     * Copia il testo di una poesia
     */
    async copyPoemText(poemId) {
        try {
            const finalCopy = this.buildShareText(poemId, { includeAttribution: true, includePermalink: false });

            // Clipboard API moderna
            if (navigator.clipboard?.writeText) {
                await navigator.clipboard.writeText(finalCopy);
                this.showToast('copy', 'Poesia copiata!');
            } else {
                this.fallbackCopyText(finalCopy);
            }
        } catch (error) {
            console.error('Errore nella copia:', error);
            this.showToast('error', 'Errore nella copia del testo');
        }
    }

    /**
     * Costruisce il testo completo per copia / condivisione.
     * Opzioni:
     *  - includeAttribution (bool)
     *  - includePermalink (bool)
     *  - maxLength (numero, per truncation soft - applicato solo al corpo poesia)
     */
    buildShareText(poemId, { includeAttribution = true, includePermalink = true, maxLength = null } = {}) {
        const poemCard = document.querySelector(`[data-poem-id="${poemId}"]`);
        if (!poemCard) return '';

        const title = poemCard.querySelector('.card-title')?.textContent?.trim() || '';
        const poemTextElement = poemCard.querySelector('.poem-text');
        if (!poemTextElement) return '';

        let rawHtml = poemTextElement.innerHTML.replace(/<br\s*\/?>/gi, '\n');
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = rawHtml;
        let cleanText = (tempDiv.textContent || tempDiv.innerText || '').trim();

        if (maxLength && cleanText.length > maxLength) {
            cleanText = cleanText.slice(0, maxLength - 1).trimEnd() + '…';
        }

        const author = poemCard.getAttribute('data-poem-author')
            || poemCard.querySelector('.fw-medium')?.textContent?.trim()
            || 'Poeta Anonimo';
        const type = poemCard.querySelector('.badge-poem-type')?.textContent?.trim() || '';

        const parts = [];
        if (title) parts.push(title);
        if (cleanText) parts.push(cleanText);
        parts.push(`- ${author}`);
        if (includeAttribution) parts.push('(da Ale\'s Haikus)');
        if (includePermalink) parts.push(this.getPoemPermalink(poemId));

        return parts.join('\n\n');
    }

    /**
     * Fallback per la copia testo
     */
    fallbackCopyText(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        textArea.style.top = '-9999px';
        document.body.appendChild(textArea);
        
        try {
            textArea.focus();
            textArea.select();
            
            const successful = document.execCommand('copy');
            if (successful) {
                this.showToast('copy', 'Testo copiato negli appunti!');
            } else {
                throw new Error('Comando copia fallito');
            }
        } catch (err) {
            console.error('Fallback copy fallito:', err);
            this.showToast('error', 'Impossibile copiare il testo');
        } finally {
            document.body.removeChild(textArea);
        }
    }

    /**
     * Condivide una poesia
     */
    async sharePoem(poemId) {
        const poemUrl = this.getPoemPermalink(poemId);
        
        try {
            if (navigator.share) {
                await navigator.share({
                    title: 'Poesia da Ale\'s Haikus',
                    text: 'Guarda questa bellissima poesia!',
                    url: poemUrl
                });
            } else {
                // Fallback: copia URL
                if (navigator.clipboard) {
                    await navigator.clipboard.writeText(poemUrl);
                    this.showToast('copy', 'Link copiato negli appunti!');
                } else {
                    this.fallbackCopyText(poemUrl);
                }
            }
        } catch (error) {
            if (error.name !== 'AbortError') { // Ignora cancellazione utente
                console.error('Errore nella condivisione:', error);
                this.showToast('error', 'Errore nella condivisione');
            }
        }
    }

    /**
     * Inizializza elementi del popup share e delega eventi
     */
    initializeSharePopup() {
        this.shareState.overlay = document.getElementById('sharePopupOverlay');
        this.shareState.popup = document.getElementById('sharePopup');
        this.shareState.extra = document.getElementById('shareExtra');
        this.shareState.closeBtn = document.getElementById('closeSharePopup');

        if (!this.shareState.overlay || !this.shareState.popup) return; // Markup non presente

        // Close events
        this.shareState.overlay.addEventListener('click', () => this.closeSharePopup());
        if (this.shareState.closeBtn) {
            this.shareState.closeBtn.addEventListener('click', () => this.closeSharePopup());
        }

        // ESC key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.shareState.popup?.classList.contains('active')) {
                this.closeSharePopup();
            }
        });

        // Delegation per icone social
        this.shareState.popup.addEventListener('click', (e) => {
            const icon = e.target.closest('.icon[data-network]');
            if (!icon) return;
            const network = icon.dataset.network;
            if (!network || !this.shareState.activePoemId) return;
            this.handleNetworkShare(network, this.shareState.activePoemId);
        });

        // Keyboard activation (Enter/Space)
        this.shareState.popup.addEventListener('keydown', (e) => {
            if ((e.key === 'Enter' || e.key === ' ') && e.target.classList?.contains('icon')) {
                e.preventDefault();
                const network = e.target.dataset.network;
                if (network) this.handleNetworkShare(network, this.shareState.activePoemId);
            }
        });
    }

    /**
     * Costruisce permalink (astrazione futura)
     */
    getPoemPermalink(poemId) {
        if (!poemId) return window.location.href;
        const patternFn = this.config.share.permalinkPattern;
        const relative = patternFn ? patternFn(poemId) : `/poesia/${poemId}`;
        return `${this.config.share.origin}${relative}`;
    }

    /**
     * Apre popup share
     */
    openSharePopup(poemId) {
        this.shareState.activePoemId = poemId;
        if (!this.shareState.overlay || !this.shareState.popup) {
            // Fallback: usa share API
            this.sharePoem(poemId);
            return;
        }
        this.shareState.overlay.classList.add('active');
        this.shareState.overlay.style.display = 'block';
        this.shareState.popup.classList.add('active');
        this.shareState.popup.setAttribute('aria-hidden', 'false');
        this.shareState.overlay.setAttribute('aria-hidden', 'false');
        // Non mettere focus su un'icona di piattaforma per evitare selezione visiva iniziale
        // Sposta invece il focus sul contenitore (gestibile da screen reader) se possibile
        if (this.shareState.popup.hasAttribute('tabindex')) {
            setTimeout(() => this.shareState.popup.focus({ preventScroll: true }), 50);
        }

        if (this.shareState.extra) {
            this.shareState.extra.style.display = 'none';
            this.shareState.extra.textContent = '';
        }
    }

    /** Chiude popup share */
    closeSharePopup() {
        if (!this.shareState.overlay || !this.shareState.popup) return;
        this.shareState.popup.classList.remove('active');
        this.shareState.popup.setAttribute('aria-hidden', 'true');
        this.shareState.overlay.classList.remove('active');
        this.shareState.overlay.setAttribute('aria-hidden', 'true');
        setTimeout(() => {
            if (!this.shareState.overlay.classList.contains('active')) {
                this.shareState.overlay.style.display = 'none';
            }
        }, 200);
        this.shareState.activePoemId = null;
    }

    /** Gestisce share per network specifico */
    async handleNetworkShare(network, poemId) {
        const permalink = this.getPoemPermalink(poemId);
        // Testo completo (senza permalink incorporato) per canali che lo supportano
        let baseText = this.buildShareText(poemId, { includeAttribution: true, includePermalink: false });
        if (!baseText) baseText = this.config.share.defaultShareText;

        let shareUrl = '';
        const encodedPermalink = encodeURIComponent(permalink);

        switch (network) {
            case 'twitter': {
                // Limite ~280 caratteri: riserviamo spazio per due newline + permalink
                const reserve = permalink.length + 4; // margine
                const maxTweet = 280 - reserve;
                let tweetBody = baseText;
                if (tweetBody.length > maxTweet) {
                    tweetBody = tweetBody.slice(0, maxTweet - 1).trimEnd() + '…';
                }
                const tweet = encodeURIComponent(`${tweetBody}\n\n${permalink}`);
                shareUrl = `https://twitter.com/intent/tweet?text=${tweet}`;
                break; }
            case 'whatsapp': {
                const waText = encodeURIComponent(`${baseText}\n\n${permalink}`);
                shareUrl = `https://api.whatsapp.com/send?text=${waText}`;
                break; }
            case 'facebook': {
                // Facebook UI moderna ignora spesso quote nei param standard; proviamo og meta + u param
                // Aggiungiamo anche testo copiato negli appunti come fallback esperienziale
                const fbUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodedPermalink}`;
                try {
                    const clipboardPayload = `${baseText}\n\n${permalink}`;
                    if (navigator.clipboard?.writeText) {
                        await navigator.clipboard.writeText(clipboardPayload);
                        if (this.shareState.extra) {
                            this.shareState.extra.style.display = 'block';
                            this.shareState.extra.textContent = 'Testo copiato: incollalo nel box di Facebook se non appare automaticamente.';
                        }
                    }
                } catch(_) {/*silent*/}
                shareUrl = fbUrl;
                break; }
            case 'instagram': {
                // Copia sempre testo completo + permalink
                try {
                    const instaText = `${baseText}\n\n${permalink}`;
                    if (navigator.clipboard?.writeText) {
                        await navigator.clipboard.writeText(instaText);
                        if (this.shareState.extra) {
                            this.shareState.extra.style.display = 'block';
                            this.shareState.extra.textContent = 'Testo e link copiati! Incollali nelle storie o nel post.';
                        }
                        this.showToast('copy', 'Testo copiato!');
                    } else {
                        this.fallbackCopyText(instaText);
                    }
                } catch (err) {
                    console.error('Instagram copy failed:', err);
                    this.showToast('error', 'Impossibile preparare il testo per Instagram');
                }
                return; }
            default:
                console.warn('Network share non supportato:', network);
                return;
        }
        const w = 640, h = 540;
        const left = (screen.width/2)-(w/2);
        const top = (screen.height/2)-(h/2);
        window.open(shareUrl, 'shareWindow', `menubar=no,toolbar=no,resizable=yes,scrollbars=yes,width=${w},height=${h},top=${top},left=${left}`);

        // Feedback opzionale
        if (this.shareState.extra) {
            this.shareState.extra.style.display = 'block';
            this.shareState.extra.textContent = 'Condivisione aperta. Se manca il testo, incollalo manualmente (già copiato dove possibile).';
        }
    }

    /**
     * Espande una poesia nel modal
     */
    expandPoem(poemId) {
        try {
            // Ricostruisci lista visibile se vuota o DOM cambiato
            this.buildExpandedIds();
            const idx = this.expandedState.ids.indexOf(String(poemId));
            if (idx === -1) throw new Error('Poesia non trovata nella lista visibile');
            this.expandedState.currentIndex = idx;
            this.updateExpandedContent(idx, { animate: false });
            this.updateExpandedNavButtons();
            this.showModal('expandedPoemModal');
            this.expandedState.isOpen = true;
            this.bindExpandedModalLifecycle();
        } catch (error) {
            console.error('Errore nell\'espansione poesia:', error);
            this.showToast('error', 'Errore nell\'apertura della poesia');
        }
    }

    /** Costruisce / aggiorna lista ids visibili */
    buildExpandedIds() {
        // Seleziona solo le card principali (non i pulsanti nel dropdown) per evitare duplicazioni
        const cards = document.querySelectorAll('.poem-card[data-poem-id]');
        this.expandedState.ids = Array.from(cards).map(c => c.getAttribute('data-poem-id'));
    }

    /** Aggiorna contenuto modal sulla base dell'indice */
    updateExpandedContent(index, { animate = true } = {}) {
        if (index < 0 || index >= this.expandedState.ids.length) return;
        const poemId = this.expandedState.ids[index];
        const poemCard = document.querySelector(`[data-poem-id="${poemId}"]`);
        if (!poemCard) return;

        const title = poemCard.querySelector('.card-title')?.textContent || 'Poesia';
        const content = poemCard.querySelector('.poem-text')?.innerHTML || '';
        const author = poemCard.querySelector('.fw-medium')?.textContent || 'Poeta Anonimo';
        const type = poemCard.querySelector('.badge-poem-type')?.textContent || 'Libero';
        const dateElement = poemCard.querySelector('.bi-clock')?.parentElement;
        const date = dateElement ? dateElement.textContent.match(/\d{2}\/\d{2}\/\d{4}/)?.[0] || '' : '';

        if (this.elements.expandedTitle) {
            this.elements.expandedTitle.textContent = title;
        }
        if (this.elements.expandedContent) {
            if (animate) {
                this.elements.expandedContent.classList.add('switching');
                setTimeout(() => {
                    this.elements.expandedContent.innerHTML = content;
                    this.postProcessExpandedContent();
                    this.elements.expandedContent.classList.remove('switching');
                    this.elements.expandedContent.classList.add('expanded-switching-enter');
                    setTimeout(() => this.elements.expandedContent.classList.remove('expanded-switching-enter'), 450);
                }, 140);
            } else {
                this.elements.expandedContent.innerHTML = content;
                this.postProcessExpandedContent();
            }
        }
        if (this.elements.expandedAuthor) {
            this.elements.expandedAuthor.textContent = author;
        }
        if (this.elements.expandedInfo) {
            this.elements.expandedInfo.innerHTML = `
                <i class="bi bi-bookmark me-1"></i>${type}
                ${date ? ` • ${date}` : ''}
                <span class="ms-2 small">${index + 1}/${this.expandedState.ids.length}</span>
            `;
        }

        // Pulsanti copia / like
        if (this.elements.expandedCopyBtn) {
            this.elements.expandedCopyBtn.onclick = () => this.copyPoemText(poemId);
        }
        if (this.elements.expandedLikeBtn) {
            this.elements.expandedLikeBtn.onclick = () => {
                const originalBtn = poemCard.querySelector('.like-btn');
                if (originalBtn) this.toggleLike(poemId, originalBtn);
            };
        }

        // Like count sync
        const originalLikeCount = poemCard.querySelector('.like-count');
        if (originalLikeCount && this.elements.expandedLikeCount) {
            this.elements.expandedLikeCount.textContent = originalLikeCount.textContent;
        }
    }

    /** Post-processing del contenuto lungo: aggiunge gradient fade e pulsante toggle se necessario */
    postProcessExpandedContent() {
        const container = this.elements.expandedContent;
        if (!container) return;
        // Rimuovi eventuali wrapper precedenti
        const existingWrapper = container.querySelector('.expanded-scroll-inner');
        if (existingWrapper) return; // già processato per questa poesia

        // Se il contenuto è molto lungo, incapsula
        if (container.scrollHeight > container.clientHeight * 1.15) {
            const html = container.innerHTML;
            container.innerHTML = '';
            const inner = document.createElement('div');
            inner.className = 'expanded-scroll-inner';
            inner.innerHTML = html;
            container.appendChild(inner);

            const fade = document.createElement('div');
            fade.className = 'expanded-fade';
            container.appendChild(fade);

            const toggle = document.createElement('button');
            toggle.type = 'button';
            toggle.className = 'btn btn-haiku btn-sm expanded-toggle-more';
            toggle.innerHTML = '<i class="bi bi-arrows-expand"></i> Leggi tutto';
            toggle.addEventListener('click', () => {
                container.classList.toggle('expanded-open');
                const open = container.classList.contains('expanded-open');
                toggle.innerHTML = open
                    ? '<i class="bi bi-arrows-collapse"></i> Riduci'
                    : '<i class="bi bi-arrows-expand"></i> Leggi tutto';
                if (open) {
                    container.scrollTo({ top: 0, behavior: 'smooth' });
                }
            });
            // Inserisci il toggle dopo il container (nel layout actions rimane richiesto separato?) -> qui lo mettiamo in fondo al container
            const parentActions = container.parentElement?.querySelector('.expanded-poem-actions');
            if (parentActions) {
                // Inserisci prima dei pulsanti esistenti
                parentActions.insertBefore(toggle, parentActions.firstChild);
            } else {
                container.appendChild(toggle);
            }
        }
    }

    /** Naviga avanti/indietro */
    navigateExpanded(direction) {
        if (!this.expandedState.isOpen) return;
        const newIndex = this.expandedState.currentIndex + direction;
        if (newIndex < 0 || newIndex >= this.expandedState.ids.length) return;
        this.expandedState.currentIndex = newIndex;
        this.updateExpandedContent(newIndex, { animate: true });
        this.updateExpandedNavButtons();
    }

    /** Aggiorna stato pulsanti navigazione */
    updateExpandedNavButtons() {
        const prevBtn = document.getElementById('expandedNavPrev');
        const nextBtn = document.getElementById('expandedNavNext');
        if (!prevBtn || !nextBtn) return;
        prevBtn.disabled = this.expandedState.currentIndex <= 0;
        nextBtn.disabled = this.expandedState.currentIndex >= this.expandedState.ids.length - 1;
    }

    /** Bind eventi ai pulsanti nav e lifecycle del modal */
    bindExpandedModalLifecycle() {
        const prevBtn = document.getElementById('expandedNavPrev');
        const nextBtn = document.getElementById('expandedNavNext');
        const modalEl = this.elements.expandedModal;
        if (prevBtn && !prevBtn._bound) {
            prevBtn.addEventListener('click', () => this.navigateExpanded(-1));
            prevBtn._bound = true;
        }
        if (nextBtn && !nextBtn._bound) {
            nextBtn.addEventListener('click', () => this.navigateExpanded(1));
            nextBtn._bound = true;
        }
        if (modalEl && !modalEl._expandedBound) {
            modalEl.addEventListener('hidden.bs.modal', () => {
                this.expandedState.isOpen = false;
                this.expandedState.currentIndex = -1;
            });
            modalEl._expandedBound = true;
        }
    }

    /**
     * Mostra dettagli poesia (navigazione)
     */
    showPoemDetails(poemId) {
        window.location.href = `/poesia/${poemId}`;
    }

    /**
     * Applica ordinamento
     */
    applySorting(sortBy) {
        this.currentSort = sortBy;
        
        const params = new URLSearchParams(window.location.search);
        params.set('sort', sortBy);
        params.set('page', '1'); // Reset alla prima pagina
        
        const newUrl = `${window.location.pathname}?${params.toString()}`;
        
        // Aggiorna history
        history.pushState({
            bacheca: true,
            filters: this.currentFilters,
            sort: sortBy,
            page: 1
        }, '', newUrl);
        
        window.location.href = newUrl;
    }

    /**
     * Va a una pagina specifica
     */
    goToSpecificPage() {
        if (!this.elements.goToPage) return;
        
        const pageNumber = parseInt(this.elements.goToPage.value);
        
        if (pageNumber >= 1 && pageNumber <= this.totalPages) {
            this.goToPage(pageNumber);
        } else {
            this.showToast('error', 
                `Numero pagina non valido. Inserisci un valore tra 1 e ${this.totalPages}`);
            this.elements.goToPage.value = this.currentPage;
        }
    }

    /**
     * Naviga a una pagina
     */
    goToPage(pageNumber) {
        const params = new URLSearchParams(window.location.search);
        params.set('page', pageNumber);
        
        const newUrl = `${window.location.pathname}?${params.toString()}`;
        
        // Aggiorna history
        history.pushState({
            bacheca: true,
            filters: this.currentFilters,
            sort: this.currentSort,
            page: pageNumber
        }, '', newUrl);
        
        window.location.href = newUrl;
    }

    /**
     * Mostra/nasconde stato di caricamento
     */
    setLoadingState(loading) {
        this.isLoading = loading;
        
        if (this.elements.loadingIndicator) {
            this.elements.loadingIndicator.style.display = loading ? 'block' : 'none';
        }
        
        if (this.elements.poemsContainer) {
            this.elements.poemsContainer.style.opacity = loading ? '0.5' : '1';
            this.elements.poemsContainer.style.pointerEvents = loading ? 'none' : 'auto';
        }
        
        // Disabilita controlli durante caricamento
        const controls = [
            this.elements.applyFilters,
            this.elements.clearFilters,
            this.elements.typeFilter,
            this.elements.authorFilter,
            this.elements.onlyValidFilter
        ];
        
        controls.forEach(element => {
            if (element) {
                element.disabled = loading;
            }
        });
    }

    /**
     * Mostra un toast
     */
    showToast(type, message = '') {
        const toastElement = this.toasts[type];
        if (!toastElement) {
            console.warn(`Toast type '${type}' not found`);
            return;
        }

        // Aggiorna messaggio se specificato
        if (message) {
            const bodyElement = toastElement.querySelector('.toast-body');
            if (bodyElement) {
                bodyElement.textContent = message;
            }
        }

        // Mostra toast con Bootstrap se disponibile
        if (window.bootstrap && bootstrap.Toast) {
            const toast = new bootstrap.Toast(toastElement);
            toast.show();
        } else {
            // Fallback semplice
            toastElement.style.display = 'block';
            toastElement.style.opacity = '1';
            
            setTimeout(() => {
                toastElement.style.opacity = '0';
                setTimeout(() => {
                    toastElement.style.display = 'none';
                }, 300);
            }, 3000);
        }
    }

    /**
     * Mostra un modal
     */
    showModal(modalId) {
        const modalElement = document.getElementById(modalId);
        if (!modalElement) return;

        if (window.bootstrap && bootstrap.Modal) {
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
        } else {
            // Fallback semplice
            modalElement.style.display = 'block';
            modalElement.classList.add('show');
            document.body.classList.add('modal-open');
        }
    }

    /**
     * Gestisce resize finestra
     */
    handleResize() {
        // Riadatta layout se necessario
        if (window.innerWidth < 768) {
            // Mobile: forza vista lista se griglia troppo stretta
            if (this.elements.poemsContainer?.classList.contains('poems-grid')) {
                // Potresti voler cambiare automaticamente vista
            }
        }
    }

    /**
     * Carica stato da history
     */
    loadStateFromHistory(state) {
        if (state.filters) {
            this.currentFilters = { ...this.currentFilters, ...state.filters };
        }
        if (state.sort) {
            this.currentSort = state.sort;
        }
        if (state.page) {
            this.currentPage = state.page;
        }
        
        this.syncFiltersToUI();
    }

    /**
     * Aggiorna UI generale
     */
    updateUI() {
        // Aggiorna contatori, stato, ecc.
        this.updatePoemCount();
        this.setupCurrentPageIndicators();
    }

    /**
     * Aggiorna contatore poesie
     */
    updatePoemCount() {
        if (this.elements.poemCount) {
            const visiblePoems = document.querySelectorAll('.poem-card-wrapper').length;
            this.elements.poemCount.textContent = visiblePoems;
        }
    }

    /**
     * Setup indicatori pagina corrente
     */
    setupCurrentPageIndicators() {
        // Evidenzia pagina corrente nei controlli di paginazione
        document.querySelectorAll('.pagination .page-item').forEach(item => {
            const link = item.querySelector('.page-link');
            if (link && parseInt(link.textContent) === this.currentPage) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    /**
     * Cleanup e distruttore
     */
    destroy() {
        // Rimuovi event listeners se necessario
        clearTimeout(this.searchTimeout);
        
        // Pulisci cache
        this.elements = {};
        this.toasts = {};
        
        console.log('BachecaManager distrutto');
    }
}

// Auto-inizializzazione quando DOM è pronto (FIX per import dinamico)
function initBachecaManager() {
    if (!window.bachecaManager) {
        window.bachecaManager = new BachecaManager();
        window.bachecaManager.init();
    }
}

window.BachecaManager = BachecaManager;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initBachecaManager);
} else {
    initBachecaManager();
}

// (Opzionale) esposizione funzione copia globale
window.copyPoem = (id) => {
    if (window.bachecaManager) {
        window.bachecaManager.copyPoemText(id);
    }
};