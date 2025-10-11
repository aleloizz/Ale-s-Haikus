(() => {
  const STATE = {
    deferredPrompt: null,
    dismissedUntil: 0,
    cooldownOverrideDays: null
  };

  const STORAGE_KEY = 'pwaInstallDismissedUntil';
  const STORAGE_CFG_DAYS = 'pwaInstallCooldownDays';
  const DEFAULT_COOLDOWN_DAYS = 7; // lowered default from 30 → 7

  function now() { return Date.now(); }

  function loadDismissedUntil() {
    try { STATE.dismissedUntil = parseInt(localStorage.getItem(STORAGE_KEY) || '0', 10); } catch {}
  }

  function getMetaCooldownDays() {
    const el = document.querySelector('meta[name="pwa-install-cooldown-days"]');
    if (!el) return null;
    const v = parseInt(el.getAttribute('content') || '', 10);
    return Number.isFinite(v) && v > 0 ? v : null;
  }

  function getQueryOverride() {
    const params = new URLSearchParams(window.location.search);
    if (params.has('pwaInstallReset')) return { reset: true };
    if (params.has('pwaCooldownDays')) {
      const v = parseInt(params.get('pwaCooldownDays') || '', 10);
      if (Number.isFinite(v) && v > 0) return { cooldownDays: v };
    }
    return {};
  }

  function getStoredCooldownDays() {
    try {
      const v = parseInt(localStorage.getItem(STORAGE_CFG_DAYS) || '', 10);
      return Number.isFinite(v) && v > 0 ? v : null;
    } catch { return null; }
  }

  function getCooldownDays() {
    if (STATE.cooldownOverrideDays) return STATE.cooldownOverrideDays;
    const q = getQueryOverride();
    if (q.cooldownDays) return q.cooldownDays;
    const meta = getMetaCooldownDays();
    if (meta) return meta;
    const stored = getStoredCooldownDays();
    if (stored) return stored;
    return DEFAULT_COOLDOWN_DAYS;
  }

  function saveDismissed(days) {
    const d = Number.isFinite(days) && days > 0 ? days : getCooldownDays();
    const until = now() + d * 24 * 60 * 60 * 1000;
    try { localStorage.setItem(STORAGE_KEY, String(until)); } catch {}
    STATE.dismissedUntil = until;
  }

  function isStandalone() {
    return window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
  }

  function isIosSafari() {
    const ua = window.navigator.userAgent;
    const iOS = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    const isSafari = /^((?!chrome|android).)*safari/i.test(ua);
    return iOS && isSafari;
  }

  function createStyles() {
    if (document.getElementById('pwa-install-styles')) return;
    const style = document.createElement('style');
    style.id = 'pwa-install-styles';
    style.textContent = `
      .pwa-install-btn{position:fixed;right:16px;bottom:16px;z-index:2147483000;background:#111;color:#fff;border:0;border-radius:999px;padding:10px 14px;box-shadow:0 6px 20px rgba(0,0,0,.2);display:flex;gap:.5rem;align-items:center;font:600 14px/1.2 system-ui, -apple-system, Segoe UI, Roboto, Arial,sans-serif;cursor:pointer;opacity:.98;}
      .pwa-install-btn:hover{opacity:1}
      .pwa-install-btn .icon{width:18px;height:18px;display:inline-block}
      .pwa-install-ios-hint{position:fixed;left:50%;bottom:16px;transform:translateX(-50%);background:#111;color:#fff;border-radius:12px;padding:10px 12px;font:500 13px/1.3 system-ui, -apple-system, Segoe UI, Roboto, Arial,sans-serif;box-shadow:0 6px 20px rgba(0,0,0,.2);z-index:2147483000}
      @media (prefers-color-scheme: light){.pwa-install-btn,.pwa-install-ios-hint{background:#222;color:#fff}}
      @media (prefers-reduced-motion: reduce){.pwa-install-btn,.pwa-install-ios-hint{transition:none}}
    `;
    document.head.appendChild(style);
  }

  function buildInstallButton() {
    createStyles();
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'pwa-install-btn';
    btn.id = 'pwaInstallButton';
    btn.setAttribute('aria-label', "Installa l'app");
    btn.innerHTML = `
      <svg class="icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M12 3v12m0 0 4-4m-4 4-4-4M4 21h16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      <span>Installa app</span>
    `;
    btn.addEventListener('click', async () => {
      if (!STATE.deferredPrompt) { btn.remove(); return; }
      try {
        STATE.deferredPrompt.prompt();
        const { outcome } = await STATE.deferredPrompt.userChoice;
        STATE.deferredPrompt = null;
        if (outcome === 'accepted') {
          btn.remove();
        } else {
          saveDismissed(30);
          btn.remove();
        }
      } catch {
        saveDismissed(30);
        btn.remove();
      }
    });
    document.body.appendChild(btn);
  }

  function showIosHint() {
    // Don't nag repeatedly
    if (STATE.dismissedUntil > now()) return;
    createStyles();
    const hint = document.createElement('div');
    hint.className = 'pwa-install-ios-hint';
    hint.role = 'status';
    hint.innerHTML = "Aggiungi alla schermata Home: tocca Condividi → 'Aggiungi a Home'.";
    document.body.appendChild(hint);
    setTimeout(() => { hint.remove(); }, 8000);
    // Respect configured cool-down for iOS hint as well
    saveDismissed();
  }

  async function registerServiceWorker() {
    if (!('serviceWorker' in navigator)) return;
    try {
      await navigator.serviceWorker.register('/sw.js');
    } catch (e) {
      // no-op
    }
  }

  function wireInstallFlow() {
    if (isStandalone()) return; // Already installed
    loadDismissedUntil();

    // Query overrides: reset and cooldown
    const q = getQueryOverride();
    if (q.reset) {
      try { localStorage.removeItem(STORAGE_KEY); } catch {}
      STATE.dismissedUntil = 0;
    }
    if (q.cooldownDays) {
      STATE.cooldownOverrideDays = q.cooldownDays;
      try { localStorage.setItem(STORAGE_CFG_DAYS, String(q.cooldownDays)); } catch {}
    }
    if (isIosSafari()) {
      // Delay a bit to avoid immediate pop-in
      setTimeout(showIosHint, 2000);
      return; // No beforeinstallprompt on iOS
    }
    window.addEventListener('beforeinstallprompt', (e) => {
      // Respect cool-down
      if (STATE.dismissedUntil > now()) return;
      e.preventDefault();
      STATE.deferredPrompt = e;
      // Show our lightweight button
      buildInstallButton();
    });

    window.addEventListener('appinstalled', () => {
      try { localStorage.removeItem(STORAGE_KEY); } catch {}
      const btn = document.getElementById('pwaInstallButton');
      if (btn) btn.remove();
    });
  }

  // Boot
  registerServiceWorker();
  wireInstallFlow();

  // Small debug API for console use
  window.PWAInstall = {
    reset() { try { localStorage.removeItem(STORAGE_KEY); } catch {}; STATE.dismissedUntil = 0; },
    setCooldownDays(n) { if (Number.isFinite(n) && n > 0) { STATE.cooldownOverrideDays = n; try { localStorage.setItem(STORAGE_CFG_DAYS, String(n)); } catch {} } },
    getCooldownDays,
  };
})();
