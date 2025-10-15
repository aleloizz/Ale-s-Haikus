/* landing.js - v2.9 aggiornamento landing-template */
(function(){
  const supportsIO = 'IntersectionObserver' in window;
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Year auto update
  const yEl = document.getElementById('year');
  if (yEl) yEl.textContent = new Date().getFullYear();

  // Lazy reveal cards
  const toReveal = [].slice.call(document.querySelectorAll('.feature-card, .seo-card'));
  if (supportsIO && toReveal.length) {
    const io = new IntersectionObserver((entries)=>{
      entries.forEach(e=>{
        if(e.isIntersecting){
          e.target.classList.add('reveal');
          io.unobserve(e.target);
        }
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: .15 });
    toReveal.forEach(el=>io.observe(el));
  } else {
    toReveal.forEach(el=>el.classList.add('reveal'));
  }

  // CTA basic analytics (placeholder)
  document.addEventListener('click', (e)=>{
    const a = e.target.closest('a[data-cta]');
    if(!a) return;
    // Hook for future analytics (no network now to keep clean)
    console.log('[CTA]', a.getAttribute('data-cta'));
  }, { passive:true });

  // SVG scroll drawing effect (progress legato alla porzione della sezione visibile)
  const path = document.getElementById('forma-path');
  const section = document.querySelector('.scroll-section');
  if (path && section) {
    try {
      const len = path.getTotalLength();
      if (!len || !isFinite(len)) {
        path.classList.add('force-visible');
        return;
      }
      const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      const isMobile = window.matchMedia('(max-width: 800px)').matches;
      // Setup iniziale completamente non disegnato
      path.style.strokeDasharray = len + ' ' + len;
      path.style.strokeDashoffset = len;
      path.getBoundingClientRect();
      requestAnimationFrame(()=> path.classList.add('path-ready'));

      if (prefersReduced) {
        path.style.strokeDashoffset = 0;
        path.style.strokeDasharray = 'none';
        return;
      }

    // Parametri regolabili (mobile-friendly)
  const START_BUFFER = isMobile ? 0 : 180;   // ritarda di più l'inizio su desktop
  const END_BUFFER   = isMobile ? 0 : 90;    // termina un po' dopo su desktop
  let EASING_POWER   = isMobile ? 4.2 : 6.5; // curva più lenta, soprattutto su mobile
      const EASING = (p)=> {
        // easing morbido + potenza per rallentare la progressione su mobile
        const eased = (1 - Math.cos(Math.PI * p)) / 2; // easeInOutSine
        return Math.pow(eased, EASING_POWER);
      };

      let sectionTop = 0;
      let sectionHeight = 0;
      let drawable = 0;

      function recalc() {
        sectionTop = section.offsetTop;
        sectionHeight = section.offsetHeight;
        const vpH = window.innerHeight || document.documentElement.clientHeight;
        drawable = sectionHeight - vpH - START_BUFFER - END_BUFFER;
      }

      function computeProgress() {
        const scrollY = window.scrollY || window.pageYOffset;
        let rel = scrollY - sectionTop - START_BUFFER;
        if (rel < 0) rel = 0;
        if (drawable <= 0) return 1;
        // Normalizza alla lunghezza effettiva in modo che completi sempre a fine sezione
        let pct = rel / drawable;
        if (pct > 1) pct = 1; else if (pct < 0) pct = 0;
        return EASING(pct);
      }

      function draw() {
        const pct = computeProgress();
        const drawLen = len * pct;
        path.style.strokeDashoffset = len - drawLen;
      }

      function onScroll() { draw(); }
      function onResize() { recalc(); draw(); }

    recalc();
    // se lo spazio scrollabile è poco su mobile, aumenta la potenza per rallentare ulteriormente la progressione
  if (isMobile && drawable < 320) { EASING_POWER = 4.8; }
      draw();
      window.addEventListener('scroll', onScroll, { passive:true });
      window.addEventListener('resize', onResize, { passive:true });
    } catch(e){ /* silent */ }
  }

  // Share Project popup
  (function(){
    const overlay = document.getElementById('sharePopupOverlay');
    const modal = document.getElementById('sharePopup');
    const btn = document.getElementById('openShare');
    const closeBtn = document.getElementById('closeSharePopup');
    const baseUrl = ((window.location && window.location.origin) ? window.location.origin : 'https://www.aleshaikus.me') + '/landing';
    const shareText = "Scopri Ale's Haikus: crea e condividi le tue migliori poesie!";

    function getUtmUrl(source = 'instagram', medium = 'social'){
      const url = new URL(baseUrl, window.location.origin);
      url.searchParams.set('utm_source', source);
      url.searchParams.set('utm_medium', medium);
      url.searchParams.set('utm_campaign', 'landing_share');
      return url.toString();
    }
    function copyToClipboard(text){
      if (navigator.clipboard && navigator.clipboard.writeText) {
        return navigator.clipboard.writeText(text);
      }
      return new Promise((resolve,reject)=>{
        try{
          const ta = document.createElement('textarea');
          ta.value = text;
          ta.setAttribute('readonly','');
          ta.style.position = 'absolute';
          ta.style.left = '-9999px';
          document.body.appendChild(ta);
          ta.select();
          const ok = document.execCommand('copy');
          document.body.removeChild(ta);
          ok ? resolve() : reject();
        }catch(err){ reject(err); }
      });
    }
    function downloadAsset(assetUrl, filename){
      try{
        const a = document.createElement('a');
        a.href = assetUrl;
        a.download = filename || '';
        a.rel = 'noopener';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }catch(_){ /* ignore */ }
    }
    async function attemptShareImage(assetUrl, filename, shareText){
      try{
        if (!navigator.share || !navigator.canShare) return false;
        const res = await fetch(assetUrl, { credentials: 'same-origin' });
        if (!res.ok) return false;
        const blob = await res.blob();
        const type = blob.type || 'image/png';
        const file = new File([blob], filename || 'image.png', { type });
        if (!navigator.canShare({ files: [file] })) return false;
        await navigator.share({ files: [file], title: "Ale's Haikus", text: shareText || '' });
        return true;
      } catch(_){
        return false;
      }
    }

    function open(e){
      if (e && typeof e.preventDefault === 'function') e.preventDefault();
      // Per coerenza con la bacheca: apri sempre il popup custom
      show();
    }
    function show(){
      if(overlay){ overlay.removeAttribute('hidden'); overlay.classList.add('active'); overlay.setAttribute('aria-hidden','false'); overlay.style.display=''; }
      if(modal){
        modal.removeAttribute('hidden'); modal.classList.add('active'); modal.setAttribute('aria-hidden','false'); modal.style.display=''; modal.focus();
        const extra = document.getElementById('shareExtra');
        const ig = document.getElementById('instagramShareFormat');
        if (extra){ extra.style.display = 'none'; extra.textContent = ''; }
        if (ig){ ig.style.display = 'none'; }
      }
    }
    function hide(){
      if(overlay){ overlay.classList.remove('active'); overlay.setAttribute('aria-hidden','true'); overlay.style.display=''; overlay.setAttribute('hidden',''); }
      if(modal){
        modal.classList.remove('active'); modal.setAttribute('aria-hidden','true'); modal.style.display=''; modal.setAttribute('hidden','');
        const ig = document.getElementById('instagramShareFormat');
        const extra = document.getElementById('shareExtra');
        if (ig){ ig.style.display = 'none'; }
        if (extra){ extra.style.display = 'none'; }
      }
    }
    function buildUrl(net){
      const u = encodeURIComponent(baseUrl);
      const t = encodeURIComponent(shareText);
      switch(net){
        case 'facebook': return `https://www.facebook.com/sharer/sharer.php?u=${u}`;
        case 'twitter': return `https://twitter.com/intent/tweet?url=${u}&text=${t}`;
        case 'whatsapp': return `https://api.whatsapp.com/send?text=${t}%20${u}`;
        case 'telegram': return `https://t.me/share/url?url=${u}&text=${t}`;
        default: return baseUrl;
      }
    }
    function showCopiedMessage(text){
      const msg = document.getElementById('shareExtra');
      if(msg){
        msg.textContent = text || 'Link copiato negli appunti!';
        msg.style.display = 'block';
      }
    }
    function fallbackCopy(){ copyToClipboard(baseUrl).then(()=>showCopiedMessage()).catch(()=>{}); }
    function handleClick(e){
      const item = e.target.closest('.icon');
      if(!item) return;
      const net = item.getAttribute('data-network');
      if (net === 'copy') {
        const url = getUtmUrl('copy', 'social');
        copyToClipboard(url)
          .then(()=>showCopiedMessage(`Link copiato: ${url}`))
          .catch(()=>{ fallbackCopy(); showCopiedMessage(`Link copiato: ${url}`); });
        return;
      }
      if (net === 'instagram') {
        // Mostra opzioni formato e copia link con UTM generica per IG
        const ig = document.getElementById('instagramShareFormat');
        if (ig){ ig.style.display = 'block'; }
        const igGeneric = getUtmUrl('instagram','social');
        copyToClipboard(igGeneric)
          .then(()=>showCopiedMessage('Link copiato! Ora scegli un formato per Instagram.'))
          .catch(()=>{ fallbackCopy(); showCopiedMessage('Link copiato! Ora scegli un formato per Instagram.'); });
        return;
      }
      const url = buildUrl(net);
      window.open(url, '_blank', 'noopener,noreferrer');
    }

    // Bind Instagram format buttons: download template and copy UTM link specific to format
    const igBox = document.getElementById('instagramShareFormat');
    if (igBox && !igBox.dataset.bound){
      igBox.addEventListener('click', async (e)=>{
        const btn = e.target.closest('[data-ig-format]');
        if(!btn) return;
        const fmt = btn.getAttribute('data-ig-format');
        let asset = '';
        let filename = '';
        let medium = '';
        if (fmt === 'story') {
          asset = '/static/images/share/landing-template.png';
          filename = 'aleshaikus-story.png';
          medium = 'story';
        } else { return; }

        const urlWithUtm = getUtmUrl('instagram', medium);
        // Copia comunque il link (sticker link o descrizione)
        copyToClipboard(urlWithUtm).catch(()=>{});
        const shared = await attemptShareImage(asset, filename, `Scopri Ale's Haikus → ${urlWithUtm}`);
        if (shared){
          showCopiedMessage('Condivisione aperta. Scegli Instagram e aggiungi lo sticker Link: è già copiato.');
        } else {
          downloadAsset(asset, filename);
          showCopiedMessage(`Condivisione diretta non supportata. Immagine ${fmt === 'story' ? 'Storia 1080×1920' : 'Post 1080×1350'} scaricata. Apri Instagram e aggiungi lo sticker Link: è già copiato.`);
        }
      });
      igBox.dataset.bound = '1';
    }

    btn && btn.addEventListener('click', open);
    // Delegation fallback in case direct binding fails for any reason
    document.addEventListener('click', (e)=>{
      const t = e.target.closest('#openShare');
      if(t){ open(e); }
    });
    overlay && overlay.addEventListener('click', hide);
    closeBtn && closeBtn.addEventListener('click', hide);
    modal && modal.addEventListener('click', handleClick);
    // Keyboard support: Enter/Space on focused share item
    modal && modal.addEventListener('keydown', (e)=>{
      if(e.key === 'Enter' || e.key === ' '){
        const active = document.activeElement;
        if(active && active.classList && active.classList.contains('icon')){
          e.preventDefault();
          handleClick({ target: active });
        }
      }
    });
    document.addEventListener('keydown', (e)=>{ if(e.key==='Escape') hide(); });
  })();
})();
