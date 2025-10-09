/* landing.js - v2.3 import share popup fix*/
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

  // (Removed) Lazy illustration handling: no .lazy-illustration element present in current template

  // CTA basic analytics (placeholder)
  document.addEventListener('click', (e)=>{
    const a = e.target.closest('a[data-cta]');
    if(!a) return;
    // Hook for future analytics (no network now to keep clean)
    console.log('[CTA]', a.getAttribute('data-cta'));
  }, { passive:true });

  // (Removed) Anime.js animations – no longer used

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
      const START_BUFFER = isMobile ? 0 : 80;   // usa tutto lo spazio su mobile
      const END_BUFFER   = isMobile ? 0 : 40;
      let EASING_POWER   = isMobile ? 2.6 : 1.1; // >1 = più lento all'inizio mantenendo completamento
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
      // se lo spazio scrollabile è poco su mobile, aumenta leggermente la potenza per maggiore fluidità percepita
      if (isMobile && drawable < 320) { EASING_POWER = 2.4; }
      draw();
      window.addEventListener('scroll', onScroll, { passive:true });
      window.addEventListener('resize', onResize, { passive:true });
    } catch(e){ /* silent */ }
  }

  // Share Project (re-uses simplified modal pattern from bacheca)
  (function(){
    const overlay = document.getElementById('sharePopupOverlay');
    const modal = document.getElementById('sharePopup');
    const btn = document.getElementById('openShare');
    const closeBtn = document.getElementById('closeSharePopup');
    const shareUrl = ((window.location && window.location.origin) ? window.location.origin : 'https://www.aleshaikus.me') + '/landing';
    const shareText = "Scopri Ale's Haikus: crea e condividi le tue migliori poesie!";

    function open(e){
      if (e && typeof e.preventDefault === 'function') e.preventDefault();
      // Per coerenza con la bacheca: apri sempre il popup custom
      show();
    }
    function show(){
      if(overlay){ overlay.style.display='block'; overlay.setAttribute('aria-hidden','false'); }
      if(modal){
        modal.style.display='block'; modal.setAttribute('aria-hidden','false'); modal.focus();
        const extra = document.getElementById('shareExtra');
        const ig = document.getElementById('instagramShareFormat');
        if (extra){ extra.style.display = 'none'; extra.textContent = ''; }
        if (ig){ ig.style.display = 'none'; }
      }
    }
    function hide(){
      if(overlay){ overlay.style.display='none'; overlay.setAttribute('aria-hidden','true'); }
      if(modal){
        modal.style.display='none'; modal.setAttribute('aria-hidden','true');
        const ig = document.getElementById('instagramShareFormat');
        const extra = document.getElementById('shareExtra');
        if (ig){ ig.style.display = 'none'; }
        if (extra){ extra.style.display = 'none'; }
      }
    }
    function buildUrl(net){
      const u = encodeURIComponent(shareUrl);
      const t = encodeURIComponent(shareText);
      switch(net){
        case 'facebook': return `https://www.facebook.com/sharer/sharer.php?u=${u}`;
        case 'twitter': return `https://twitter.com/intent/tweet?url=${u}&text=${t}`;
        case 'whatsapp': return `https://api.whatsapp.com/send?text=${t}%20${u}`;
        case 'telegram': return `https://t.me/share/url?url=${u}&text=${t}`;
        default: return shareUrl;
      }
    }
    function showCopiedMessage(text){
      const msg = document.getElementById('shareExtra');
      if(msg){
        msg.textContent = text || 'Link copiato negli appunti!';
        msg.style.display = 'block';
      }
    }
    function fallbackCopy(){
      try{
        const ta = document.createElement('textarea');
        ta.value = shareUrl;
        ta.setAttribute('readonly','');
        ta.style.position = 'absolute';
        ta.style.left = '-9999px';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        showCopiedMessage();
      }catch(_){ /* ignore */ }
    }
    function handleClick(e){
      const item = e.target.closest('.icon');
      if(!item) return;
      const net = item.getAttribute('data-network');
      if (net === 'copy') {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(shareUrl).then(()=>showCopiedMessage(`Condivideremo: ${shareUrl}`)).catch(()=>{ fallbackCopy(); showCopiedMessage(`Condivideremo: ${shareUrl}`); });
        } else {
          fallbackCopy();
          showCopiedMessage(`Condivideremo: ${shareUrl}`);
        }
        return;
      }
      if (net === 'instagram') {
        // Mostra opzioni formato e copia link, come pattern bacheca
        const ig = document.getElementById('instagramShareFormat');
        if (ig){ ig.style.display = 'block'; }
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(shareUrl).then(()=>showCopiedMessage('Link copiato! Scegli un formato per Instagram.')).catch(()=>{ fallbackCopy(); showCopiedMessage('Link copiato! Scegli un formato per Instagram.'); });
        } else {
          fallbackCopy();
          showCopiedMessage('Link copiato! Scegli un formato per Instagram.');
        }
        return;
      }
      const url = buildUrl(net);
      window.open(url, '_blank', 'noopener,noreferrer');
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
