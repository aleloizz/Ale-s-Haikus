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

  // SVG scroll drawing effect
  const path = document.getElementById('forma-path');
  if (path) {
    try {
      const length = path.getTotalLength();
      path.style.strokeDasharray = length + ' ' + length;
      path.style.strokeDashoffset = length;
      path.getBoundingClientRect(); // force layout
      const onScroll = () => {
        const doc = document.documentElement;
        const scrollTop = doc.scrollTop || document.body.scrollTop;
        const scrollHeight = doc.scrollHeight - doc.clientHeight;
        const pct = scrollHeight > 0 ? scrollTop / scrollHeight : 0;
        const draw = length * pct;
        path.style.strokeDashoffset = length - draw;
        if (pct >= 0.995) {
          path.style.strokeDasharray = 'none';
        } else {
          path.style.strokeDasharray = length + ' ' + length;
        }
      };
      window.addEventListener('scroll', onScroll, { passive:true });
      // initial in case user reloads mid-scroll
      onScroll();
    } catch(e){ /* ignore */ }
  }
})();
