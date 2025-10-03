/* landing.js - v0.2 */
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

  // Lazy illustration handling
  const illus = document.querySelector('.lazy-illustration');
  if (illus && supportsIO) {
    const img = illus.querySelector('img');
    const obs = new IntersectionObserver((entries)=>{
      entries.forEach(ent=>{
        if(ent.isIntersecting){
          if (img && img.loading !== 'eager') {
            img.decoding = 'async';
            // Already has src; just ensure onload transition
            img.addEventListener('load', ()=>illus.classList.add('loaded'), { once:true });
            if (img.complete) illus.classList.add('loaded');
          }
          obs.disconnect();
        }
      });
    }, { rootMargin:'150px 0px' });
    obs.observe(illus);
  } else if (illus) {
    illus.classList.add('loaded');
  }

  // CTA basic analytics (placeholder)
  document.addEventListener('click', (e)=>{
    const a = e.target.closest('a[data-cta]');
    if(!a) return;
    // Hook for future analytics (no network now to keep clean)
    console.log('[CTA]', a.getAttribute('data-cta'));
  }, { passive:true });

  // Progressive Anime.js usage (only if loaded & motion not reduced)
  window.addEventListener('load', ()=>{
    if (prefersReduced) return;
    if (window.anime) {
      try {
        window.anime({
          targets: '.feature-card.reveal',
            translateY: [18,0], opacity: [0,1], delay: window.anime.stagger(55), duration: 820,
            easing: 'cubicBezier(.16,.8,.32,1)'
        });
      } catch(err){/* silent */}
    }
  });

  // SVG scroll drawing effect (semplificato: progress legato alla porzione della sezione visibile, sempre da zero)
  const path = document.getElementById('forma-path');
  const section = document.querySelector('.scroll-section');
  if (path && section) {
    try {
      const len = path.getTotalLength();
      if (!len || !isFinite(len)) {
        path.classList.add('force-visible');
        console.warn('[SVGDraw] Path length non valido – forzo visibilità immediata');
        return;
      }
      const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      // Setup iniziale completamente non disegnato
      path.style.strokeDasharray = len + ' ' + len;
      path.style.strokeDashoffset = len;
      path.getBoundingClientRect();
      requestAnimationFrame(()=> path.classList.add('path-ready'));
      console.log('[SVGDraw] Inizializzazione completata', { length: len });

      if (prefersReduced) {
        path.style.strokeDashoffset = 0;
        path.style.strokeDasharray = 'none';
        console.log('[SVGDraw] prefers-reduced-motion attivo: disegno completato immediatamente');
        return;
      }

      // Parametri regolabili
      const START_BUFFER = 80;   // px di scroll interni prima che inizi a disegnare
      const END_BUFFER   = 40;   // px finali “morti” per rallentare completamento
      const EASING = (p)=> Math.pow(p,0.95); // leggera spinta iniziale

      let sectionTop = 0;
      let sectionHeight = 0;
      let drawable = 0;
      let started = false;
      let finished = false;

      function recalc() {
        sectionTop = section.offsetTop;
        sectionHeight = section.offsetHeight;
        const vpH = window.innerHeight || document.documentElement.clientHeight;
        drawable = sectionHeight - vpH - START_BUFFER - END_BUFFER;
        console.log('[SVGDraw] Recalc', { sectionTop, sectionHeight, drawable, vpH });
      }

      function computeProgress() {
        const scrollY = window.scrollY || window.pageYOffset;
        let rel = scrollY - sectionTop - START_BUFFER;
        if (rel < 0) rel = 0;
        if (drawable <= 0) return 1; // se la sezione non è abbastanza alta disegna tutto
        let pct = rel / drawable;
        if (pct > 1) pct = 1; else if (pct < 0) pct = 0;
        return EASING(pct);
      }

      function draw() {
        const pct = computeProgress();
        const drawLen = len * pct;
        path.style.strokeDashoffset = len - drawLen;
        if (!started && pct > 0) {
          started = true;
          console.log('[SVGDraw] Animazione avviata', { pct, drawLen });
        }
        if (!finished && pct >= 1) {
          finished = true;
          console.log('[SVGDraw] Animazione completata', { pct });
        }
        if (pct >= 1) {
          // opzionale togli dash: path.style.strokeDasharray = 'none';
        }
      }

      function onScroll() { draw(); }
      function onResize() { recalc(); draw(); }

      recalc();
      draw();
      window.addEventListener('scroll', onScroll, { passive:true });
      window.addEventListener('resize', onResize, { passive:true });

      // Debug facoltativo: aggiungi ?debugShape all'URL
      if (location.search.includes('debugShape')) {
        console.log('[ShapeDebug]', { len, sectionTop, sectionHeight });
      }
    } catch(e){ /* silent */ }
  }
})();
