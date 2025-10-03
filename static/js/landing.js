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

  // SVG scroll drawing effect (Opzione B: sempre inizia da zero anche se reload a metà)
  const path = document.getElementById('forma-path');
  const section = document.querySelector('.scroll-section');
  if (path && section) {
    try {
      const length = path.getTotalLength();
      if (!length || !isFinite(length) || length === 0) {
        path.classList.add('force-visible');
        return;
      }

      // Setup iniziale (sempre completamente "non disegnato")
      path.style.strokeDasharray = length + ' ' + length;
      path.style.strokeDashoffset = length;
      path.getBoundingClientRect(); // layout sync
      requestAnimationFrame(()=> path.classList.add('path-ready'));

      const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (prefersReduced) {
        path.style.strokeDashoffset = 0;
        path.style.strokeDasharray = 'none';
        return;
      }

      const START_BUFFER = 120; // px prima che il tratto inizi a disegnarsi
      const clamp = (v,min,max)=> v<min?min:(v>max?max:v);

      // Cattura la posizione iniziale della sezione quando attiviamo l'animazione
      let baselineTop = null;
      let active = false;
      let lastDraw = -1;

      function computePct() {
        if (baselineTop === null) return 0; // finché non attivato
        const rect = section.getBoundingClientRect();
        const vpH = window.innerHeight || document.documentElement.clientHeight;
        const totalScrollable = rect.height - vpH;
        if (totalScrollable <= 0) return 1;
        // offset relativo (quanto la sezione si è spostata rispetto alla baseline)
        let relative = baselineTop - rect.top - START_BUFFER;
        if (relative < 0) relative = 0;
        const raw = relative / (totalScrollable - START_BUFFER);
        const pct = clamp(raw,0,1);
        return pct;
      }

      function updateFrame() {
        if (!active) return;
        const pct = computePct();
        const draw = length * pct;
        if (draw !== lastDraw) {
            path.style.strokeDashoffset = length - draw;
            lastDraw = draw;
        }
        requestAnimationFrame(updateFrame);
      }

      // IntersectionObserver per avviare SEMPRE da zero
      const io = new IntersectionObserver((entries)=>{
        entries.forEach(ent=>{
          if (ent.isIntersecting) {
            if (!active) {
              // Congela baseline al momento dell'entrata (ignoriamo posizione reale se reload a metà)
              const rect = section.getBoundingClientRect();
              baselineTop = rect.top; // baseline fissata
              active = true;
              lastDraw = -1;
              // Assicura stato iniziale non disegnato
              path.style.strokeDashoffset = length;
              updateFrame();
            }
          } else if (ent.boundingClientRect.top > 0) {
            // Se l'utente torna sopra completamente, resettiamo per consentire replay
            active = false;
            baselineTop = null;
            lastDraw = -1;
            path.style.strokeDashoffset = length;
          }
        });
      }, { threshold: 0 });
      io.observe(section);

      window.addEventListener('resize', ()=>{ lastDraw = -1; }, { passive:true });

      // Fallback: se per qualche ragione non entra mai in viewport (es. salto ancora più giù),
      // dopo 3s mostriamo comunque il path non disegnato (così non resta opaco 0 nascosto)
      setTimeout(()=>{ if (!active) path.classList.add('path-ready'); },3000);
    } catch(e){ /* silent */ }
  }
})();
