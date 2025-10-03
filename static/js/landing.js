/* landing.js - progressive enhancement & performance safe */
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

  // SVG scroll drawing effect (progress legato alla sola sezione intro)
  const path = document.getElementById('forma-path');
  const section = document.querySelector('.scroll-section');
  if (path && section) {
    try {
      const length = path.getTotalLength();
      // Evita problemi se il path ha lunghezza 0 (SVG non caricato correttamente)
      if (!length || length === 0 || !isFinite(length)) {
        path.classList.add('force-visible');
        return;
      }
      // Imposta dash iniziale prima di mostrare gradualmente
      path.style.strokeDasharray = length + ' ' + length;
      path.style.strokeDashoffset = length;
      path.getBoundingClientRect(); // force layout
      requestAnimationFrame(()=> path.classList.add('path-ready'));
      // Fallback: se entro 1.2s non si è mosso nulla, mostra comunque
      setTimeout(()=>{
        if (parseFloat(getComputedStyle(path).strokeDashoffset) === length) {
          path.classList.add('path-ready');
        }
      },1200);

      const clamp = (v,min,max)=> v < min ? min : (v > max ? max : v);

      let lastPct = -1; // evita reflow inutili
      const computeProgress = () => {
        const rect = section.getBoundingClientRect();
        const viewportH = window.innerHeight || document.documentElement.clientHeight;
        // Quando il top della sezione raggiunge 0 inizia (rect.top)
        // La sezione è più alta del viewport: progress avanza fino a quando il bottom esce verso l'alto
        const totalScrollable = rect.height - viewportH; // spazio utile interno
        // offset interno scroll = distanza percorsa dall'inizio "visivo" della sezione
        const internalOffset = clamp(-rect.top, 0, totalScrollable <= 0 ? 1 : totalScrollable);
        const pct = totalScrollable > 0 ? internalOffset / totalScrollable : 1;
        return clamp(pct,0,1);
      };

      const update = () => {
        const pct = computeProgress();
        if (pct === lastPct) return;
        lastPct = pct;
        const draw = length * pct;
        path.style.strokeDashoffset = length - draw;
        // Manteniamo strokeDasharray per evitare flash su reload; opzionale rimozione a fine.
        // if (pct >= 0.999) path.style.strokeDasharray = 'none';
      };

      // Ottimizza con rAF durante scroll
      let ticking = false;
      const onScroll = () => {
        if (!ticking) {
          ticking = true;
          requestAnimationFrame(()=>{update(); ticking = false;});
        }
      };
      window.addEventListener('scroll', onScroll, { passive:true });
      window.addEventListener('resize', ()=>{ lastPct = -1; update(); }, { passive:true });
      update();
    } catch(e){ /* ignore */ }
  }
})();
