// pwa-install.js v1.3 (2025-10-11) - CTA sempre visibile, su mobile in basso a sinistra
(() => {
  'use strict';

  // State & configuration
  const STATE = { deferredPrompt: null, dismissedUntil: 0, cooldownOverrideDays: null };
  const STORAGE_KEY = 'pwaInstallDismissedUntil';
  const STORAGE_CFG_DAYS = 'pwaInstallCooldownDays';
  const DEFAULT_COOLDOWN_DAYS = 7;

  // Utils
  const now = () => Date.now();
  const loadDismissedUntil = () => {
    try { STATE.dismissedUntil = parseInt(localStorage.getItem(STORAGE_KEY) || '0', 10) || 0; } catch {}
  };
  const getMetaCooldownDays = () => {
    const el = document.querySelector('meta[name="pwa-install-cooldown-days"]');
    if (!el) return null;
    const v = parseInt(el.getAttribute('content') || '', 10);
    return Number.isFinite(v) && v > 0 ? v : null;
  };
  const getQueryOverride = () => {
    const p = new URLSearchParams(window.location.search);
    if (p.has('pwaInstallReset')) return { reset: true };
    if (p.has('pwaCooldownDays')) {
      const v = parseInt(p.get('pwaCooldownDays') || '', 10);
      if (Number.isFinite(v) && v > 0) return { cooldownDays: v };
    }
    return {};
  };
  const getStoredCooldownDays = () => {
    try {
      const v = parseInt(localStorage.getItem(STORAGE_CFG_DAYS) || '', 10);
      return Number.isFinite(v) && v > 0 ? v : null;
    } catch { return null; }
  };
  const getCooldownDays = () => {
    if (STATE.cooldownOverrideDays) return STATE.cooldownOverrideDays;
    const q = getQueryOverride();
    if (q.cooldownDays) return q.cooldownDays;
    const m = getMetaCooldownDays();
    if (m) return m;
    const s = getStoredCooldownDays();
    if (s) return s;
    return DEFAULT_COOLDOWN_DAYS;
  };
  const saveDismissed = (days) => {
    const d = Number.isFinite(days) && days > 0 ? days : getCooldownDays();
    const until = now() + d * 24 * 60 * 60 * 1000;
    try { localStorage.setItem(STORAGE_KEY, String(until)); } catch {}
    STATE.dismissedUntil = until;
  };
  const isStandalone = () => (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) || (navigator.standalone === true);
  const isIosSafari = () => {
    const ua = navigator.userAgent;
    const iOS = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    const safari = /^((?!chrome|android).)*safari/i.test(ua);
    return iOS && safari;
  };

  // UI helpers
  const createStyles = () => {
    if (document.getElementById('pwa-install-styles')) return;
    const style = document.createElement('style');
    style.id = 'pwa-install-styles';
    style.textContent = `
.pwa-install-btn{position:fixed;right:16px;bottom:16px;z-index:2147483000;background:#111;color:#fff;border:0;border-radius:999px;padding:10px 14px;box-shadow:0 6px 20px rgba(0,0,0,.2);display:flex;gap:.5rem;align-items:center;font:600 14px/1.2 system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;cursor:pointer;opacity:.98}
.pwa-install-btn:hover{opacity:1}
.pwa-install-btn .icon{width:18px;height:18px;display:inline-block}
.pwa-install-ios-hint{position:fixed;left:50%;bottom:16px;transform:translateX(-50%);background:#111;color:#fff;border-radius:12px;padding:10px 12px;font:500 13px/1.3 system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;box-shadow:0 6px 20px rgba(0,0,0,.2);z-index:2147483000}
@media (prefers-color-scheme: light){.pwa-install-btn,.pwa-install-ios-hint{background:#222;color:#fff}}
@media (prefers-reduced-motion: reduce){.pwa-install-btn,.pwa-install-ios-hint{transition:none}}
@media (max-width: 768px){.pwa-install-btn{left:calc(16px + env(safe-area-inset-left)); right:auto; bottom:calc(16px + env(safe-area-inset-bottom));}}
`;
    document.head.appendChild(style);
  };
  const getCTAButtons = () => Array.from(document.querySelectorAll('[data-pwa-install]'));
  const hideCTAs = () => { getCTAButtons().forEach(el => { el.style.display = 'none'; }); };
  const showCTAs = () => { getCTAButtons().forEach(el => { el.style.display = ''; }); };

  let pendingClick = false;

  const triggerInstall = async (btn) => {
    if (!STATE.deferredPrompt) return false;
    try {
      STATE.deferredPrompt.prompt();
      const res = await STATE.deferredPrompt.userChoice;
      STATE.deferredPrompt = null;
      if (btn) btn.removeAttribute('disabled');
      // Se installata, nascondi CTA; se annullata, lasciale visibili e non impostare cooldown
      const accepted = !!res && res.outcome === 'accepted';
      if (accepted) hideCTAs();
      return accepted;
    } catch {
      if (btn) btn.removeAttribute('disabled');
      // Niente cooldown su errore/annullamento
      return false;
    }
  };

  const buildInstallButton = () => {
    createStyles();
    if (document.getElementById('pwaInstallButton')) return;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'pwa-install-btn';
    btn.id = 'pwaInstallButton';
    btn.setAttribute('aria-label', "Installa l'app");
    btn.innerHTML = `
<svg class="icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M12 3v12m0 0 4-4m-4 4-4-4M4 21h16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
<span>Installa app</span>
`;
    btn.addEventListener('click', () => {
      if (!STATE.deferredPrompt) { pendingClick = true; return; }
      triggerInstall(btn);
    });
    document.body.appendChild(btn);
  };

  const showIosHint = () => {
    if (STATE.dismissedUntil > now()) return;
    createStyles();
    const hint = document.createElement('div');
    hint.className = 'pwa-install-ios-hint';
    hint.setAttribute('role', 'status');
    hint.textContent = "Aggiungi alla schermata Home: tocca Condividi → 'Aggiungi a Home'.";
    document.body.appendChild(hint);
    setTimeout(() => { if (hint && hint.parentNode) hint.parentNode.removeChild(hint); }, 8000);
    saveDismissed();
  };

  // SW registration
  const registerServiceWorker = () => {
    if (!('serviceWorker' in navigator)) return;
    try { navigator.serviceWorker.register('/sw.js'); } catch {}
  };

  // Main flow
  const wireInstallFlow = () => {
    if (isStandalone()) return; // Already installed
    loadDismissedUntil();

    // Overrides via query params
    const q = getQueryOverride();
    if (q.reset) { try { localStorage.removeItem(STORAGE_KEY); } catch {}; STATE.dismissedUntil = 0; }
    if (q.cooldownDays) { STATE.cooldownOverrideDays = q.cooldownDays; try { localStorage.setItem(STORAGE_CFG_DAYS, String(q.cooldownDays)); } catch {} }

    // Always wire CTA buttons early so clicks before the event are handled
    getCTAButtons().forEach(el => {
      el.addEventListener('click', (e) => {
        e.preventDefault();
        if (isIosSafari()) { showIosHint(); return; }
        if (STATE.deferredPrompt) { el.setAttribute('disabled', 'true'); triggerInstall(el); return; }
        // No prompt yet: remember the intent and prompt as soon as eligible
        pendingClick = true;
      });
    });

    if (isIosSafari()) {
      setTimeout(showIosHint, 2000);
      showCTAs();
      return;
    }

    // Mostra subito il pulsante flottante anche prima dell'evento
    buildInstallButton();

    // Mostra le CTA quando l'evento è disponibile
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      STATE.deferredPrompt = e;
      buildInstallButton();
      showCTAs();
      // If user already clicked before the event, prompt immediately
      if (pendingClick) {
        pendingClick = false;
        triggerInstall();
      }
    });

    window.addEventListener('appinstalled', () => {
      try { localStorage.removeItem(STORAGE_KEY); } catch {}
      const btn = document.getElementById('pwaInstallButton');
      if (btn && btn.parentNode) btn.parentNode.removeChild(btn);
      hideCTAs();
    });
  };

  // Boot
  registerServiceWorker();
  wireInstallFlow();

  // Debug API
  window.PWAInstall = {
    reset() { try { localStorage.removeItem(STORAGE_KEY); } catch {}; STATE.dismissedUntil = 0; },
    setCooldownDays(n) { if (Number.isFinite(n) && n > 0) { STATE.cooldownOverrideDays = n; try { localStorage.setItem(STORAGE_CFG_DAYS, String(n)); } catch {} } },
    getCooldownDays,
    prompt: () => triggerInstall(),
  };
})();
