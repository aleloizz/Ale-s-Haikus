/* landing.js - v1.1 ottimizzazione animazione svg */
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
      let EASING_POWER   = isMobile ? 2.0 : 1.1; // >1 = più lento all'inizio mantenendo completamento
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
})();
