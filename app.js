const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5ydXpqdHFld2pha2Z3c2hmYWd6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg5MjAyMzcsImV4cCI6MjA5NDQ5NjIzN30.GC0IRyXF1QppjbvQJNoYhe_FbWIAa6mjOZQkplrEbfM';
const isEn = document.documentElement.lang === 'en';

// ===== Origen del alta: UTM, clic de anuncio y página de entrada =====
// Se lee de la URL al cargar y viaja con el alta a join-waitlist. Solo se
// guarda en el navegador (90 días, para no perderlo al cambiar de página) si
// la persona ha aceptado las cookies; si no, vale para esta visita. Una visita
// con UTM o gclid nueva sustituye a la anterior (último clic de campaña).
var ATTR_STORE = '2t_attr';
var ATTR_KEYS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'gclid', 'fbclid'];
var attribution = (function() {
  var q = new URLSearchParams(window.location.search), now = {}, campaign = false;
  ATTR_KEYS.forEach(function(k) { var v = q.get(k); if (v) { now[k] = v.slice(0, 255); campaign = true; } });
  now.landing_path = window.location.pathname;
  try {
    var ref = document.referrer && new URL(document.referrer).hostname;
    if (ref && ref !== window.location.hostname) now.referrer_host = ref;
  } catch (_) {}
  var consent = /(?:^|; )cookie_consent=accepted/.test(document.cookie);
  var saved = null;
  try { saved = JSON.parse(localStorage.getItem(ATTR_STORE) || 'null'); } catch (_) {}
  if (saved && Date.now() - (saved.t || 0) > 90 * 864e5) saved = null;
  var keep = saved && !campaign ? saved.a : now;
  if (consent && keep === now) { try { localStorage.setItem(ATTR_STORE, JSON.stringify({ t: Date.now(), a: now })); } catch (_) {} }
  return keep;
})();
function attributionForSignup() {
  var a = {};
  Object.keys(attribution).forEach(function(k) { a[k] = attribution[k]; });
  a.signup_path = window.location.pathname;
  return a;
}

// ===== Carrusel automático: nada de scroll lateral a mano =====
// Avanza solo y en bucle mientras está a la vista; se para al pasar el ratón o
// al enfocarlo. Tocar un punto, deslizar el dedo o usar las flechas del teclado
// cambia de tarjeta y desde ahí manda la persona (deja de avanzar solo). Con
// movimiento reducido no avanza solo.
function autoCarousel(el, opts) {
  if (!el || el._auto) return el && el._auto;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var current = 0, timer = null, inView = false, held = false, stopped = reduce;
  function items() { return Array.prototype.filter.call(el.querySelectorAll(opts.item), function(n) { return n.offsetWidth > 0; }); }
  // Posiciones de parada distintas: las últimas tarjetas comparten el final
  function stops() {
    var max = el.scrollWidth - el.clientWidth, pad = parseFloat(getComputedStyle(el).scrollPaddingLeft) || 0, out = [];
    items().forEach(function(n) {
      var p = Math.round(Math.max(0, Math.min(max, n.getBoundingClientRect().left - el.getBoundingClientRect().left + el.scrollLeft - pad)));
      if (!out.length || p - out[out.length - 1] > 2) out.push(p);
    });
    return out;
  }
  var dots = document.createElement('div');
  dots.className = 'cdots';
  if (opts.dotsIn) opts.dotsIn.appendChild(dots); else el.insertAdjacentElement('afterend', dots);
  function renderDots() {
    var n = stops().length;
    if (dots.children.length !== n) {
      dots.innerHTML = '';
      for (var i = 0; i < n; i++) {
        var b = document.createElement('button');
        b.type = 'button';
        b.setAttribute('aria-label', (isEn ? 'Show card ' : 'Ver tarjeta ') + (i + 1));
        b.addEventListener('click', (function(i) { return function() { stop(); go(i); }; })(i));
        dots.appendChild(b);
      }
    }
    dots.hidden = n < 2;
    Array.prototype.forEach.call(dots.children, function(b, i) { b.setAttribute('aria-current', String(i === current)); });
  }
  function go(i, instant) {
    var s = stops();
    if (!s.length) return;
    current = (i + s.length) % s.length;
    el.scrollTo({ left: s[current], behavior: instant || reduce ? 'auto' : 'smooth' });
    renderDots();
  }
  function sync() {
    clearInterval(timer);
    timer = null;
    if (!stopped && inView && !held && !document.hidden) timer = setInterval(function() { go(current + 1); }, opts.delay || 3000);
  }
  function stop() { stopped = true; sync(); }
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function(e) { inView = e[0].isIntersecting; if (inView) renderDots(); sync(); }, { threshold: 0.5 }).observe(el);
  } else inView = true;
  el.addEventListener('mouseenter', function() { held = true; sync(); });
  el.addEventListener('mouseleave', function() { held = false; sync(); });
  el.addEventListener('focusin', function() { held = true; sync(); });
  el.addEventListener('focusout', function() { held = false; sync(); });
  el.addEventListener('keydown', function(e) {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    e.preventDefault();
    stop();
    go(current + (e.key === 'ArrowRight' ? 1 : -1));
  });
  document.addEventListener('visibilitychange', sync);
  var x0 = null, y0 = 0;
  el.addEventListener('touchstart', function(e) { x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; }, { passive: true });
  el.addEventListener('touchend', function(e) {
    if (x0 === null) return;
    var dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0;
    x0 = null;
    if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) { stop(); go(current + (dx < 0 ? 1 : -1)); }
  }, { passive: true });
  window.addEventListener('resize', function() { renderDots(); go(current, true); });
  renderDots();
  sync();
  el._auto = { reset: function() { current = 0; go(0, true); } };
  return el._auto;
}

(function() {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const isMobile = window.matchMedia('(max-width: 767px)').matches;
  gsap.registerPlugin(ScrollTrigger);
  window.__appReady = true;
  // En móvil, ignorar el resize de la barra de direcciones evita que ScrollTrigger
  // recalcule y provoque saltos/contenido en blanco al hacer scroll.
  ScrollTrigger.config({ ignoreMobileResize: true });

  // Modal
  const modal = document.getElementById('beta-modal');
  function openModal(prefilledEmail) {
    if (prefilledEmail) {
      const i = modal.querySelector('input[name="email"]');
      if (i) i.value = prefilledEmail;
    }
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
  function closeModal() {
    modal.classList.remove('active');
    const mm = document.getElementById('mobile-menu');
    if (!mm || !mm.classList.contains('open')) document.body.style.overflow = '';
  }
  document.getElementById('modal-close').addEventListener('click', closeModal);
  modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
  document.querySelectorAll('.open-modal').forEach(btn => btn.addEventListener('click', e => { e.preventDefault(); openModal(); }));

  // Hero form & beta-form-2 → open modal with prefill (so user gets the same success state)
  ['hero-form', 'beta-form-2'].forEach(id => {
    const f = document.getElementById(id);
    if (!f) return;
    f.addEventListener('submit', e => {
      e.preventDefault();
      const email = f.querySelector('input[name="email"]').value;
      openModal(email);
      setTimeout(() => document.getElementById('modal-form').requestSubmit(), 250);
    });
  });

  // Smooth scroll
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const href = a.getAttribute('href');
      if (href.length > 1) {
        const t = document.querySelector(href);
        if (t) { e.preventDefault(); window.scrollTo({ top: t.getBoundingClientRect().top + window.scrollY - 64, behavior: reduceMotion ? 'auto' : 'smooth' }); }
      }
    });
  });

  // Nav — el estilo (degradado) lo define el CSS; aquí solo lo referenciamos
  const nav = document.getElementById('nav');

  // Navbar: arranca compacto (clase nav-compact en el HTML) y se despliega
  // al primer scroll, quedándose expandido para siempre.
  let navExpanded = false;
  function expandNav() {
    if (navExpanded || !nav) return;
    navExpanded = true;
    nav.classList.remove('nav-compact');
  }
  if (nav) {
    if (reduceMotion || window.scrollY > 20) {
      // Sin animación o ya scrolleado al cargar: expandir sin transición.
      nav.classList.add('no-nav-anim');
      expandNav();
      requestAnimationFrame(function () {
        requestAnimationFrame(function () { nav.classList.remove('no-nav-anim'); });
      });
    }
    window.addEventListener('scroll', function () {
      if (window.scrollY > 20) expandNav();
    }, { passive: true });
  }

  // Animaciones: calmadas y una sola vez. Funden y suben unos pocos píxeles;
  // sin rebotes ni escalas. El hero no se anima: su texto es el LCP y el móvil
  // tiene que verse en cuanto carga la página.
  var startPos = isMobile ? 'top 90%' : 'top 82%';
  // [data-anim]: la sección se monta sola (gráficas, chips, semana) cuando
  // entra en pantalla. El CSS pinta el estado final con .is-in.
  var animEls = gsap.utils.toArray('[data-anim]');
  if (reduceMotion) {
    animEls.forEach(function(el) { el.classList.add('is-in'); });
  } else {
    animEls.forEach(function(el) {
      ScrollTrigger.create({ trigger: el, start: startPos, once: true, onEnter: function() { el.classList.add('is-in'); } });
    });
    var RY = isMobile ? 18 : 28;
    gsap.utils.toArray('[data-reveal]').forEach(function(el) {
      gsap.from(el, { y: RY, opacity: 0, duration: 0.8, ease: 'power2.out',
        scrollTrigger: { trigger: el, start: startPos, once: true } });
    });
    // Grupos: los hijos entran escalonados (set inicial evita el parpadeo)
    gsap.utils.toArray('[data-reveal-stagger]').forEach(function(group) {
      var kids = gsap.utils.toArray(group.children);
      if (!kids.length) return;
      gsap.set(kids, { opacity: 0, y: RY });
      ScrollTrigger.create({ trigger: group, start: startPos, once: true,
        onEnter: function() { gsap.to(kids, { opacity: 1, y: 0, duration: 0.8, stagger: 0.09, ease: 'power2.out' }); } });
    });
    // Hilo entre secciones: la línea se dibuja con el scroll (scrub) y la
    // frase que enlaza con lo siguiente aparece cuando la línea llega.
    gsap.utils.toArray('.bridge').forEach(function(b) {
      var line = b.querySelector('.bridge__line');
      var rest = b.querySelectorAll('.bridge__dot, .bridge__t');
      if (line) gsap.fromTo(line, { scaleY: 0 }, { scaleY: 1, ease: 'none',
        scrollTrigger: { trigger: b, start: 'top 92%', end: 'top 55%', scrub: 0.6 } });
      if (rest.length) gsap.from(rest, { opacity: 0, y: 10, duration: 0.6, stagger: 0.12, ease: 'power2.out',
        scrollTrigger: { trigger: b, start: 'top 62%', once: true } });
    });
    // Foto ancha: se acerca un poco mientras cruza la pantalla.
    gsap.utils.toArray('.band img').forEach(function(img) {
      gsap.fromTo(img, { scale: 1.06 }, { scale: 1, ease: 'none',
        scrollTrigger: { trigger: img.parentNode, start: 'top bottom', end: 'bottom top', scrub: true } });
    });
  }

  // ===== Pantallas de «Por qué»: cada una es un pequeño vídeo en bucle =====
  // Se crean pausadas; las reproduce el bloque de abajo cuando su pantalla es
  // la visible. Con movimiento reducido no se crean y se ve el estado final.
  function screenTimeline(sc, idx) {
    if (reduceMotion || !sc) return null;
    var tl = gsap.timeline({ paused: true, repeat: -1, repeatDelay: 1.4 });
    if (idx === 0) {
      var ring = sc.querySelector('.ring__fg'), num = sc.querySelector('.ring__n b');
      var txt = sc.querySelector('.decision__txt'), chg = sc.querySelectorAll('.chg'), news = sc.querySelectorAll('.chg em'), next = sc.querySelector('.next');
      var o = { v: 0 };
      tl.set(ring, { strokeDashoffset: 100 }).set(txt, { opacity: 0, x: -8 }).set(chg, { opacity: 0, y: 10 }).set(news, { opacity: 0, scale: .6 }).set(next, { opacity: 0, y: 12 })
        .call(function() { num.textContent = '0'; })
        .to(ring, { strokeDashoffset: 5, duration: 1.4, ease: 'power2.out' }, 0.2)
        .fromTo(o, { v: 0 }, { v: 95, duration: 1.4, ease: 'power2.out', immediateRender: false, onUpdate: function() { num.textContent = Math.round(o.v); } }, 0.2)
        .to(txt, { opacity: 1, x: 0, duration: 0.5, ease: 'power2.out' }, 1.0)
        .to(chg, { opacity: 1, y: 0, duration: 0.45, stagger: 0.18, ease: 'power2.out' }, 1.4)
        .to(news, { opacity: 1, scale: 1, duration: 0.4, stagger: 0.18, ease: 'back.out(2)' }, 1.8)
        .to(next, { opacity: 1, y: 0, duration: 0.5, ease: 'power2.out' }, 2.5)
        .to({}, { duration: 2.6 });
    } else if (idx === 1) {
      var n = sc.querySelector('.resp__n b'), you = sc.querySelector('.chart__you'), area = sc.querySelector('.chart__area');
      var dot = sc.querySelector('.chart__dot'), avg = sc.querySelector('.chart__avg'), ok = sc.querySelector('.pill-ok'), how = sc.querySelector('.how');
      var c = { v: 0 };
      tl.set(you, { strokeDashoffset: 1 }).set(area, { opacity: 0 }).set(avg, { opacity: 0 }).set(dot, { scale: 0, transformOrigin: '50% 50%' }).set(ok, { opacity: 0, y: 8 }).set(how, { opacity: 0, y: 10 })
        .call(function() { n.textContent = '0'; })
        .to(avg, { opacity: 1, duration: 0.5 }, 0.2)
        .to(you, { strokeDashoffset: 0, duration: 1.6, ease: 'power2.inOut' }, 0.4)
        .to(area, { opacity: 1, duration: 0.8 }, 1.2)
        .fromTo(c, { v: 0 }, { v: 10, duration: 1.6, ease: 'power2.inOut', immediateRender: false, onUpdate: function() { n.textContent = Math.round(c.v); } }, 0.4)
        .to(dot, { scale: 1, duration: 0.4, ease: 'back.out(2.5)' }, 1.95)
        .to(ok, { opacity: 1, y: 0, duration: 0.45, ease: 'power2.out' }, 2.2)
        .to(how, { opacity: 1, y: 0, duration: 0.5, ease: 'power2.out' }, 2.6)
        .to({}, { duration: 2.6 });
    } else if (idx === 2) {
      // Tres casos seguidos; cada uno deja su línea en «Guardado en tu perfil»
      var chips = sc.querySelectorAll('.qr span'), swaps = sc.querySelectorAll('.swap'), saved = sc.querySelectorAll('.saved li');
      tl.set(saved, { opacity: 0, x: -10 });
      [0, 1, 2].forEach(function(k) {
        tl.call(function() {
          chips.forEach(function(ch, j) { ch.classList.toggle('is-on', j === k); });
          swaps.forEach(function(sw, j) { sw.classList.toggle('is-on', j === k); });
        }, null, k === 0 ? 0 : '+=0');
        tl.to(saved[k], { opacity: 1, x: 0, duration: 0.45, ease: 'power2.out' }, '+=0.8');
        tl.to({}, { duration: 1.9 });
      });
      tl.to({}, { duration: 1 });
    }
    return tl;
  }

  // ===== Por qué: el móvil queda fijo y su pantalla cambia con cada paso =====
  // Escritorio: ScrollTrigger activa el paso que llega al centro y el móvil
  // enseña su pantalla. ≤860px: galería automática con puntos.
  (function() {
    var stage = document.querySelector('.reels');
    if (!stage) return;
    var phone = stage.querySelector('.reels__phone');
    var steps = gsap.utils.toArray('.reels__step');
    if (!steps.length || !phone) return;

    if (window.matchMedia('(max-width: 860px)').matches) {
      var grid = stage.querySelector('.reels__grid');
      var screens = stage.querySelectorAll('.scr');
      // Galería automática: una pantalla cada pocos segundos, con puntos debajo
      autoCarousel(grid, { item: '.scr', delay: 6000, dotsIn: stage.querySelector('.reels__nav') });
      // Cada pantalla se reproduce mientras está a la vista en la galería
      screens.forEach(function(sc, idx) {
        var tlm = screenTimeline(sc, idx);
        if (!tlm || !('IntersectionObserver' in window)) return;
        var io = new IntersectionObserver(function(entries) {
          if (entries[0].isIntersecting) tlm.play(); else tlm.pause();
        }, { threshold: 0.55 });
        io.observe(sc);
      });
      steps.forEach(function(s) { s.classList.add('on'); });
      return;
    }

    stage.classList.add('js-active');
    var screensD = stage.querySelectorAll('.scr');
    var tls = Array.prototype.map.call(screensD, function(sc, idx) { return screenTimeline(sc, idx); });
    var current = -1;
    // La pantalla visible arranca su vídeo desde el principio; las demás se paran.
    function activate(i) {
      if (i === current) return;
      current = i;
      phone.setAttribute('data-screen', String(i));
      tls.forEach(function(tl, idx) { if (!tl) return; if (idx === i) tl.restart(); else tl.pause(); });
      steps.forEach(function(s, idx) { s.classList.toggle('on', idx === i); });
    }
    // Fuera de pantalla no se reproduce nada
    ScrollTrigger.create({ trigger: stage, start: 'top bottom', end: 'bottom top',
      onToggle: function(self) { var tl = tls[current]; if (!tl) return; if (self.isActive) tl.play(); else tl.pause(); } });
    steps.forEach(function(step, i) {
      ScrollTrigger.create({ trigger: step, start: 'top center', end: 'bottom center',
        onToggle: function(self) { if (self.isActive) activate(i); } });
    });
    // La primera pantalla se monta en cuanto el móvil asoma, sin esperar al centro
    ScrollTrigger.create({ trigger: stage, start: 'top 60%', once: true, onEnter: function() { if (current === -1) activate(0); } });
    if (reduceMotion) activate(0);
  })();

  // FAQ
  document.querySelectorAll('.faq-q').forEach(q => q.addEventListener('click', () => {
    const isOpen = q.closest('.faq-item').classList.toggle('open');
    q.setAttribute('aria-expanded', isOpen);
  }));

  // FAQ — filtros por categoría (acorta la lista mostrando solo lo relevante)
  (function() {
    var chips = document.querySelectorAll('.faq-chip');
    if (!chips.length) return;
    var items = document.querySelectorAll('#faq .faq-item');
    chips.forEach(function(chip) {
      chip.addEventListener('click', function() {
        var cat = chip.getAttribute('data-filter');
        chips.forEach(function(c) { c.classList.toggle('active', c === chip); });
        items.forEach(function(item) {
          var show = cat === 'all' || item.getAttribute('data-cat') === cat;
          item.classList.toggle('hidden', !show);
          if (!show) {
            item.classList.remove('open');
            var b = item.querySelector('.faq-q');
            if (b) b.setAttribute('aria-expanded', 'false');
          }
        });
      });
    });
  })();

  // Capture referral code from URL (atribuir referidos) y spot (ver mi posición)
  const _urlParams = new URLSearchParams(window.location.search);
  const _refCode = _urlParams.get('ref') || null;
  const _spotCode = _urlParams.get('spot') || null;

  // Modal form submit
  const mForm = document.getElementById('modal-form');
  const mFormState = document.getElementById('modal-form-state');
  const mSuccess = document.getElementById('modal-success');
  const mBtn = document.getElementById('modal-submit');
  let mError = document.getElementById('modal-error');
  if (!mError) {
    mError = document.createElement('p');
    mError.id = 'modal-error';
    mError.setAttribute('role', 'alert');
    mError.style.cssText = 'font-size:14px;text-align:center;margin:4px 0 0;display:none;';
    mForm.appendChild(mError);
  }

  function showModalError(msg) { mError.textContent = msg; mError.style.display = 'block'; }
  function hideModalError() { mError.style.display = 'none'; }

  // Beta abierta: tras el alta solo hay confirmación y compartir. El acceso
  // llega por email; ya no hay puesto, waves ni plazas que contar.
  function showModalSuccess(referralCode) {
    const link = referralCode ? `https://2trainapp.com?ref=${referralCode}` : 'https://2trainapp.com';
    const statusEl = document.querySelector('#modal-success .ms-status');
    if (statusEl) statusEl.textContent = isEn ? "You're in." : 'Estás dentro.';

    document.getElementById('ms-ref').textContent = link.replace('https://', '');
    const copyBtn = document.getElementById('ms-copy');
    copyBtn.onclick = () => {
      const done = () => {
        copyBtn.textContent = isEn ? '✓ Copied' : '✓ Copiado';
        setTimeout(() => { copyBtn.textContent = isEn ? 'Copy link' : 'Copiar link'; }, 1600);
      };
      if (navigator.clipboard) navigator.clipboard.writeText(link).then(done).catch(() => {});
    };
    const waMsg = isEn
      ? encodeURIComponent(`I just joined the 2trAIn beta ⚡ An AI coach that explains every decision in your training, with your own data. Join with my link 👉 ${link}`)
      : encodeURIComponent(`Me he unido a la beta de 2trAIn ⚡ Un coach con IA que te explica cada decisión de tu entrenamiento con tus propios datos. Entra con mi enlace 👉 ${link}`);
    document.getElementById('ms-wa').href = `https://wa.me/?text=${waMsg}`;
    const twText = isEn
      ? encodeURIComponent(`I just joined the 2trAIn beta ⚡\n\nAn AI coach that explains EVERY decision in your training →`)
      : encodeURIComponent(`Me he unido a la beta de 2trAIn ⚡\n\nUn coach con IA que te explica CADA decisión de tu entrenamiento →`);
    document.getElementById('ms-x').href = `https://twitter.com/intent/tweet?text=${twText}&url=${encodeURIComponent(link)}`;

    mFormState.classList.add('hidden');
    mSuccess.classList.remove('hidden');
  }

  mForm.addEventListener('submit', async e => {
    e.preventDefault();
    hideModalError();
    const email = mForm.querySelector('input[name="email"]').value.trim();
    mBtn.querySelector('.btn-label').textContent = isEn ? 'Sending…' : 'Enviando…';
    mBtn.disabled = true; mBtn.style.opacity = '0.6';

    try {
      const res = await fetch('https://nruzjtqewjakfwshfagz.supabase.co/functions/v1/join-waitlist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        },
        body: JSON.stringify({ email, referred_by: _refCode, lang: isEn ? 'en' : 'es', hp: (mForm.querySelector('input[name="company"]') || {}).value || '', attribution: attributionForSignup() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Error desconocido');
      showModalSuccess(data.referral_code);
    } catch (err) {
      console.error('Waitlist error:', err);
      showModalError(isEn ? 'Something went wrong. Try again or contact us.' : 'Algo salió mal. Inténtalo de nuevo o escríbenos.');
      mBtn.querySelector('.btn-label').textContent = isEn ? 'Join the beta' : 'Unirme a la beta';
      mBtn.disabled = false; mBtn.style.opacity = '';
    }
  });

  // Enlace del email (?spot=CODE) → abre el modal ya confirmado, con su enlace para compartir
  if (_spotCode) {
    openModal();
    mFormState.classList.add('hidden');
    mSuccess.classList.remove('hidden');
    const statusEl = document.querySelector('#modal-success .ms-status');
    if (statusEl) statusEl.textContent = isEn ? 'Loading…' : 'Cargando…';
    (async () => {
      try {
        const res = await fetch('https://nruzjtqewjakfwshfagz.supabase.co/functions/v1/join-waitlist', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          },
          body: JSON.stringify({ referral_code: _spotCode, lang: isEn ? 'en' : 'es' }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error');
        showModalSuccess(data.referral_code);
        // Limpia ?spot= de la URL sin recargar (evita reabrir al compartir la barra)
        try {
          const u = new URL(window.location.href);
          u.searchParams.delete('spot');
          window.history.replaceState({}, '', u.pathname + (u.search || '') + u.hash);
        } catch (_) {}
      } catch (err) {
        console.error('Spot lookup error:', err);
        mSuccess.classList.add('hidden');
        mFormState.classList.remove('hidden');
        showModalError(isEn
          ? 'We could not find that link. Sign up below.'
          : 'No encontramos ese enlace. Apúntate aquí abajo.');
      }
    })();
  }

  modal.addEventListener('transitionend', () => {
    if (!modal.classList.contains('active')) {
      setTimeout(() => {
        mFormState.classList.remove('hidden');
        mSuccess.classList.add('hidden');
        mForm.reset();
        hideModalError();
        mBtn.querySelector('.btn-label').textContent = isEn ? 'Join the beta' : 'Unirme a la beta';
        mBtn.disabled = false; mBtn.style.opacity = '';
      }, 50);
    }
  });
})();

// Cuenta atrás retirada (2026-09-02). Apuntaba al 2026-09-01 y, una vez
// vencida, dejaba en el bloque de conversión la frase "La beta abre el 1 de
// septiembre · faltan / Beta disponible" en ES y EN. La escasez de esta
// página pasa a ser de plazas —la escalera de waves de #beta-offer—, que no
// caduca sola. No reintroducir un contador sin un dueño de la fecha.

// Mobile menu
(function() {
  const toggle = document.getElementById('nav-toggle');
  const menu   = document.getElementById('mobile-menu');
  const nav    = document.getElementById('nav');
  if (!toggle || !menu) return;

  function openMenu() {
    menu.classList.add('open');
    menu.setAttribute('aria-hidden', 'false');
    nav.classList.remove('nav-compact'); // si aún está compacto, despliega la barra
    nav.classList.add('nav-open');
    toggle.setAttribute('aria-label', isEn ? 'Close menu' : 'Cerrar menú');
    toggle.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
    const first = menu.querySelector('a, button');
    if (first) first.focus();
  }

  function closeMenu() {
    menu.classList.remove('open');
    menu.setAttribute('aria-hidden', 'true');
    nav.classList.remove('nav-open');
    toggle.setAttribute('aria-label', isEn ? 'Open menu' : 'Abrir menú');
    toggle.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
    toggle.focus();
  }

  toggle.addEventListener('click', function() {
    menu.classList.contains('open') ? closeMenu() : openMenu();
  });

  // Close on any link click inside the menu
  menu.querySelectorAll('a').forEach(function(a) {
    a.addEventListener('click', closeMenu);
  });

  // Escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && menu.classList.contains('open')) closeMenu();
  });
})();

// ===== Objetivos: el selector cambia el plan orientativo y su gráfica =====
(function() {
  var section = document.querySelector('#objetivos');
  if (!section) return;
  var tabs = Array.prototype.slice.call(section.querySelectorAll('.goal-opt'));
  var bar = section.querySelector('.goals__tabs');
  var panel = section.querySelector('.goals__panel');
  var textEl = section.querySelector('#goals-preview-text');
  var vizzes = section.querySelectorAll('[data-viz]');
  var photos = section.querySelectorAll('[data-photo]');
  if (!tabs.length || !textEl || !panel) return;

  var en = document.documentElement.lang === 'en';
  var copy = en ? {
    fuerza: 'Push, pull and leg blocks with weekly load progression. Every change in volume or intensity, <strong>explained with your data</strong>.',
    cardio: 'Zone 2 base, controlled intensity days and recovery built in. Conditioning that <strong>fits your week</strong>, not random HIIT.',
    prueba: 'Toward your race day: specific strength, cardio and event stations, periodized to the date, with <strong>taper when it matters</strong>.',
    mantener: 'Sustainable frequency to stay in shape or ease back in. Enough stimulus to progress, <strong>without burning out</strong>.'
  } : {
    fuerza: 'Bloques de empuje, tirón y pierna con progresión de carga. Cada cambio de volumen o intensidad, <strong>explicado con tus datos</strong>.',
    cardio: 'Base Zone 2, días de intensidad controlada y recuperación integrada. Condición que <strong>encaja en tu semana</strong>, no HIIT al azar.',
    prueba: 'Hacia tu fecha: fuerza útil, cardio y estaciones o disciplinas, periodizado al evento, con <strong>taper cuando toca</strong>.',
    mantener: 'Frecuencia sostenible para mantener forma o volver con calma. Estímulo suficiente para progresar, <strong>sin quemarte</strong>.'
  };

  function select(i, focus) {
    var btn = tabs[i];
    var key = btn.getAttribute('data-goal');
    if (!copy[key]) return;
    tabs.forEach(function(b, j) {
      var on = j === i;
      b.setAttribute('aria-selected', String(on));
      b.tabIndex = on ? 0 : -1;
    });
    if (bar) bar.style.setProperty('--i', i);
    panel.setAttribute('aria-labelledby', btn.id);
    textEl.innerHTML = copy[key];
    vizzes.forEach(function(v) { v.hidden = v.getAttribute('data-viz') !== key; });
    photos.forEach(function(p) { p.hidden = p.getAttribute('data-photo') !== key; });
    // Vuelve a dibujar la gráfica: se quita el estado final sin transición y
    // se repone en el siguiente fotograma.
    if (panel.classList.contains('is-in')) {
      panel.classList.add('is-reset');
      panel.classList.remove('is-in');
      void panel.offsetWidth;
      panel.classList.remove('is-reset');
      requestAnimationFrame(function() { panel.classList.add('is-in'); });
    }
    if (focus) btn.focus();
  }

  tabs.forEach(function(btn, i) {
    btn.addEventListener('click', function() { select(i); });
    btn.addEventListener('keydown', function(e) {
      if (e.key === 'ArrowRight') { e.preventDefault(); select((i + 1) % tabs.length, true); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); select((i - 1 + tabs.length) % tabs.length, true); }
    });
  });
})();

// ===== Demo "Míralo pensar": pensar → colapsar → generar (soporta varios escenarios) =====
(function() {
  var section = document.querySelector('#demo');
  if (!section || typeof gsap === 'undefined') return;

  var tabs = section.querySelectorAll('.demo-tab');
  var scenarios = Array.prototype.slice.call(section.querySelectorAll('.demo-scenario'));
  var demoEN = document.documentElement.lang === 'en';
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var activeTl = null;
  var hasStarted = false;

  // El carrusel avanza solo (autoCarousel), sin scroll lateral a mano: al
  // generar la sesión vuelve al primer ejercicio y arranca desde ahí.
  function restartMarquee(chat) {
    var carousel = chat && chat.querySelector('.demo-carousel');
    if (!carousel) return;
    // Carrusel automático: avanza una tarjeta cada pocos segundos
    autoCarousel(carousel, { item: '.demo-ex', delay: 2800 }).reset();
  }

  var phrasesByScenario = {
    pain: demoEN ? [
      'Reading your history…',
      'Detecting shoulder discomfort…',
      'Ruling out risky exercises…',
      'Finding safe angles…',
      'Adding a preventive warm-up…'
    ] : [
      'Leyendo tu historial…',
      'Detectando molestia en el hombro…',
      'Descartando ejercicios de riesgo…',
      'Buscando ángulos seguros…',
      'Añadiendo calentamiento preventivo…'
    ],
    race: demoEN ? [
      'Reading your goal and date…',
      'Checking strength vs cardio base…',
      'Building hybrid weekly blocks…',
      'Periodizing toward race day…',
      'Keeping one strength day…'
    ] : [
      'Leyendo objetivo y fecha…',
      'Cruzando base de fuerza y cardio…',
      'Montando bloques híbridos…',
      'Periodizando hacia la prueba…',
      'Reservando un día de fuerza…'
    ]
  };

  function showOnly(key) {
    scenarios.forEach(function(sc) {
      var on = sc.getAttribute('data-scenario') === key;
      sc.classList.toggle('on', on);
      sc.setAttribute('aria-hidden', String(!on));
    });
    tabs.forEach(function(t, i) {
      var on = t.getAttribute('data-scenario') === key;
      t.setAttribute('aria-selected', String(on));
      t.tabIndex = on ? 0 : -1;
      // La píldora blanca del selector segmentado se desliza a la pestaña activa
      if (on && t.parentNode) t.parentNode.style.setProperty('--i', i);
    });
    return section.querySelector('.demo-scenario.on');
  }

  function bindToggle(chat) {
    var toggle = chat.querySelector('.demo-reason__toggle');
    if (!toggle || toggle.dataset.bound === '1') return;
    toggle.dataset.bound = '1';
    toggle.addEventListener('click', function() {
      var box = chat.querySelector('.demo-reason');
      var body = chat.querySelector('.demo-reason__body');
      if (!box || !body || !box.classList.contains('is-interactive')) return;
      var willCollapse = !box.classList.contains('is-collapsed');
      box.classList.toggle('is-collapsed');
      toggle.setAttribute('aria-expanded', String(!willCollapse));
      if (willCollapse) {
        chat.classList.remove('is-open');
        gsap.to(body, { height: 0, opacity: 0, duration: 0.35, ease: 'power2.inOut' });
      } else {
        chat.classList.add('is-open');
        gsap.fromTo(body, { height: 0, opacity: 0 }, { height: 'auto', opacity: 1, duration: 0.35, ease: 'power2.out' });
      }
    });
  }

  function playChat(chat) {
    if (!chat) return;
    if (activeTl) {
      activeTl.kill();
      activeTl = null;
    }

    var statusEl = chat.querySelector('.demo-chat__status-text');
    var user = chat.querySelector('.demo-bubble--user');
    var reasonBox = chat.querySelector('.demo-reason');
    var reasonBody = chat.querySelector('.demo-reason__body');
    var reasonLines = gsap.utils.toArray(chat.querySelectorAll('.demo-reason__line'));
    var toggle = chat.querySelector('.demo-reason__toggle');
    var label = chat.querySelector('.demo-reason__label');
    var aiBubble = chat.querySelector('.demo-bubble--ai');
    var genWrap = chat.querySelector('.demo-gen');
    var genHead = chat.querySelector('.demo-gen__head');
    var carousel = chat.querySelector('.demo-carousel');
    var goBtn = chat.querySelector('.demo-go');
    var scenario = chat.getAttribute('data-scenario') || 'pain';
    var phrases = phrasesByScenario[scenario] || phrasesByScenario.pain;

    chat.classList.add('demo-chat--seq');
    chat.classList.remove('is-open');
    if (reasonBox) reasonBox.classList.remove('is-interactive', 'is-collapsed');
    if (toggle) toggle.setAttribute('aria-expanded', 'true');
    if (label) { gsap.set(label, { opacity: 1 }); label.textContent = demoEN ? 'Reasoning with your data' : 'Razonando con tus datos'; }
    if (statusEl) { gsap.set(statusEl, { opacity: 1 }); statusEl.textContent = demoEN ? 'Reasoning with your data' : 'Razonando con tus datos'; }
    if (aiBubble) aiBubble.classList.add('demo-pending');
    if (genWrap) genWrap.classList.add('demo-pending');
    bindToggle(chat);

    if (reduceMotion) {
      gsap.set([user, reasonBox].concat(reasonLines), { clearProps: 'all' });
      if (reasonBody) gsap.set(reasonBody, { height: 0, opacity: 0 });
      if (reasonBox) reasonBox.classList.add('is-interactive', 'is-collapsed');
      if (label) label.textContent = demoEN ? 'Reasoned with your data' : 'Razonado con tus datos';
      if (toggle) toggle.setAttribute('aria-expanded', 'false');
      if (statusEl) statusEl.textContent = demoEN ? 'Session generated ✓' : 'Sesión generada ✓';
      if (aiBubble) aiBubble.classList.remove('demo-pending');
      if (genWrap) genWrap.classList.remove('demo-pending');
      restartMarquee(chat);
      return;
    }

    gsap.set([user, reasonBox], { opacity: 0, y: 14 });
    gsap.set(reasonLines, { opacity: 0, y: 8 });
    if (reasonBody) gsap.set(reasonBody, { height: 'auto', opacity: 1 });
    gsap.set([genHead, carousel, goBtn].filter(Boolean), { opacity: 0, y: 14 });

    function setStatus(t) {
      if (!statusEl) return;
      gsap.to(statusEl, { opacity: 0, duration: 0.15, onComplete: function() {
        statusEl.textContent = t;
        gsap.to(statusEl, { opacity: 1, duration: 0.15 });
      }});
    }
    function setPhrase(t) {
      if (!label) return;
      gsap.to(label, { opacity: 0, duration: 0.15, onComplete: function() {
        label.textContent = t;
        gsap.to(label, { opacity: 1, duration: 0.15 });
      }});
    }

    // Siempre timeline inmediata (sin ScrollTrigger): más fiable al cambiar de tab
    var tl = gsap.timeline({ defaults: { ease: 'power2.out' } });
    activeTl = tl;

    tl.to(user, { opacity: 1, y: 0, duration: 0.35 });
    tl.to(reasonBox, { opacity: 1, y: 0, duration: 0.35 }, '+=0.2');

    reasonLines.forEach(function(line, i) {
      tl.call(setPhrase, [phrases[i % phrases.length]]);
      tl.to(line, { opacity: 1, y: 0, duration: 0.28 }, '+=0.04');
      tl.to({}, { duration: 0.35 });
    });

    tl.call(function() {
      if (reasonBox) reasonBox.classList.add('is-interactive', 'is-collapsed');
      if (label) { gsap.set(label, { opacity: 1 }); label.textContent = demoEN ? 'Reasoned with your data' : 'Razonado con tus datos'; }
      if (toggle) toggle.setAttribute('aria-expanded', 'false');
    }, null, '+=0.2');
    tl.to(reasonBody, { height: 0, opacity: 0, duration: 0.4, ease: 'power2.inOut' });
    tl.call(setStatus, [demoEN ? 'Generating your session…' : 'Generando tu sesión…']);

    tl.call(function() { if (aiBubble) aiBubble.classList.remove('demo-pending'); });
    tl.fromTo(aiBubble, { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.35 }, '+=0.05');

    tl.call(function() {
      if (genWrap) genWrap.classList.remove('demo-pending');
      restartMarquee(chat);
    });
    tl.to(genHead, { opacity: 1, y: 0, duration: 0.3 }, '+=0.08');
    tl.to(carousel, { opacity: 1, y: 0, duration: 0.4, ease: 'power3.out' }, '-=0.1');
    tl.call(function() {
      setStatus(demoEN ? 'Session generated ✓' : 'Sesión generada ✓');
      restartMarquee(chat);
    });
    tl.to(goBtn, { opacity: 1, y: 0, duration: 0.3 }, '+=0.05');
  }

  // Prep visual inicial: oculta lo animable hasta que entre en vista
  scenarios.forEach(function(sc) {
    var user = sc.querySelector('.demo-bubble--user');
    var reasonBox = sc.querySelector('.demo-reason');
    var aiBubble = sc.querySelector('.demo-bubble--ai');
    var genWrap = sc.querySelector('.demo-gen');
    sc.classList.add('demo-chat--seq');
    if (aiBubble) aiBubble.classList.add('demo-pending');
    if (genWrap) genWrap.classList.add('demo-pending');
    if (!reduceMotion) {
      if (user) gsap.set(user, { opacity: 0, y: 14 });
      if (reasonBox) gsap.set(reasonBox, { opacity: 0, y: 14 });
    }
  });
  showOnly('pain');

  tabs.forEach(function(tab, i) {
    tab.addEventListener('click', function() {
      var key = tab.getAttribute('data-scenario');
      if (!key || tab.getAttribute('aria-selected') === 'true') return;
      var chat = showOnly(key);
      requestAnimationFrame(function() { playChat(chat); });
    });
    tab.addEventListener('keydown', function(e) {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      e.preventDefault();
      var to = tabs[(i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
      to.focus();
      to.click();
    });
  });

  // Arranca al entrar en viewport (IntersectionObserver, sin ScrollTrigger)
  function startWhenVisible() {
    if (hasStarted) return;
    hasStarted = true;
    var chat = section.querySelector('.demo-scenario.on') || scenarios[0];
    playChat(chat);
  }

  if (reduceMotion) {
    startWhenVisible();
  } else if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function(entries) {
      for (var i = 0; i < entries.length; i++) {
        if (entries[i].isIntersecting) {
          startWhenVisible();
          io.disconnect();
          break;
        }
      }
    }, { threshold: 0.25, rootMargin: '0px 0px -10% 0px' });
    io.observe(section);
  } else {
    startWhenVisible();
  }
})();

// ===== "Pruébalo ya mismo": en móvil va DESPUÉS del chat (primero ves la demo, luego la usas) =====
(function() {
  var cta = document.querySelector('.demo-head__cta');
  var head = document.querySelector('.demo-head');
  var wrap = document.querySelector('#demo .demo-scenarios') || document.querySelector('#demo .demo-chat');
  if (!cta || !head || !wrap) return;
  var mq = window.matchMedia('(max-width: 860px)');
  function place() {
    if (mq.matches) {
      if (wrap.nextElementSibling !== cta) wrap.parentNode.insertBefore(cta, wrap.nextSibling);
    } else {
      if (cta.parentNode !== head) head.appendChild(cta);
    }
  }
  place();
  if (mq.addEventListener) mq.addEventListener('change', place);
  else if (mq.addListener) mq.addListener(place);
})();
